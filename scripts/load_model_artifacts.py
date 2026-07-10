# -*- coding: utf-8 -*-
"""Switch seed_dev -> notebook_04: carga los artefactos REALES del modelo XGBoost.

Cuando el Notebook 04 genere:
  - datos/modelos/predicciones.parquet   (upz_cod, anio, mes, nivel_riesgo,
                                          prob_critico, prob_alto, prob_medio, prob_bajo)
  - datos/modelos/shap_values.parquet    (upz_cod, anio, mes, feature, valor)

este script borra las filas sinteticas (origen='seed_dev') e inserta las reales
(origen='notebook_04'). El backend NO cambia: sigue siendo lookup por PK.

Uso:
    python scripts/load_model_artifacts.py            # carga ambos
    python scripts/load_model_artifacts.py --dry-run  # valida esquemas sin tocar la DB
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

import polars as pl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / ".env")

PRED_PARQUET = ROOT / "datos" / "modelos" / "predicciones.parquet"
SHAP_PARQUET = ROOT / "datos" / "modelos" / "shap_values.parquet"
METRICAS_JSON = ROOT / "datos" / "modelos" / "metricas.json"

# Quality-gate: umbrales minimos antes de cargar un modelo nuevo a Supabase.
# Holgados respecto a los valores ya validados (macro_f1=0.867,
# accuracy_within_1_band=1.0) -- atrapan una regresion real, no ruido normal
# entre corridas. Ajustables si el criterio del equipo cambia.
MACRO_F1_MIN = 0.75
ACCURACY_BANDA_MIN = 0.90

PRED_COLS = ["upz_cod", "anio", "mes", "nivel_riesgo",
             "prob_critico", "prob_alto", "prob_medio", "prob_bajo"]
SHAP_COLS = ["upz_cod", "anio", "mes", "feature", "valor"]
NIVELES = {"CRITICO", "ALTO", "MEDIO", "BAJO"}


def validar(df: pl.DataFrame, cols: list[str], nombre: str) -> pl.DataFrame:
    faltan = [c for c in cols if c not in df.columns]
    if faltan:
        sys.exit(f"{nombre}: faltan columnas {faltan}")
    df = df.select(cols).with_columns(pl.col("upz_cod").cast(pl.Utf8).str.zfill(3))
    if "nivel_riesgo" in cols:
        malos = set(df["nivel_riesgo"].unique().to_list()) - NIVELES
        if malos:
            sys.exit(f"{nombre}: niveles invalidos {malos}")
        sumas = df.select(
            (pl.col("prob_critico") + pl.col("prob_alto")
             + pl.col("prob_medio") + pl.col("prob_bajo")).alias("s")
        )
        fuera = sumas.filter((pl.col("s") < 0.99) | (pl.col("s") > 1.01)).height
        if fuera:
            sys.exit(f"{nombre}: {fuera} filas con probabilidades que no suman 1")
    print(f"{nombre}: {df.height:,} filas validas")
    return df


def validar_metricas(force: bool) -> None:
    """Quality-gate: no carga un modelo peor que el umbral minimo sin --force.

    Se corre ANTES de tocar la base de datos -- si no pasa, sys.exit(1) sin
    ningun DELETE/INSERT. Es la unica red de seguridad que existe hoy contra
    una regresion de modelo cargada en silencio (load_via_rest/copy_in
    sobreescriben sin comparar contra el run anterior).
    """
    if not METRICAS_JSON.exists():
        sys.exit(f"No existe {METRICAS_JSON} -- ejecuta primero: python scripts/train_model.py")

    metricas = json.loads(METRICAS_JSON.read_text(encoding="utf-8"))
    macro_f1 = metricas.get("macro_f1")
    accuracy_banda = metricas.get("accuracy_within_1_band")

    if macro_f1 is None or accuracy_banda is None:
        sys.exit(f"{METRICAS_JSON}: faltan claves 'macro_f1'/'accuracy_within_1_band'")

    problemas = []
    if macro_f1 < MACRO_F1_MIN:
        problemas.append(f"macro_f1={macro_f1:.3f} < minimo {MACRO_F1_MIN}")
    if accuracy_banda < ACCURACY_BANDA_MIN:
        problemas.append(f"accuracy_within_1_band={accuracy_banda:.3f} < minimo {ACCURACY_BANDA_MIN}")

    if problemas:
        mensaje = "Quality-gate FALLO -- " + "; ".join(problemas)
        if force:
            print(f"[AVISO] {mensaje} -- continuando por --force")
            return
        sys.exit(f"{mensaje}\nUsa --force para cargar de todas formas (no recomendado).")

    print(f"Quality-gate OK: macro_f1={macro_f1:.3f}, accuracy_within_1_band={accuracy_banda:.3f}")


def copy_in(conn, tabla: str, cols: list[str], df: pl.DataFrame, origen: str) -> None:
    df = df.with_columns(pl.lit(origen).alias("origen"))
    buf = io.BytesIO()
    df.write_csv(buf)
    buf.seek(0)
    buf.readline()
    with conn.cursor() as cur:
        # Borra TODO artefacto previo (seed_dev y notebook_04), no solo seed_dev:
        # si el set de features cambia entre versiones, el upsert dejaría filas
        # obsoletas huérfanas (p. ej. la feature 'mes' tras pasar a mes_sin/mes_cos).
        cur.execute(f"DELETE FROM {tabla} WHERE origen IN ('seed_dev', 'notebook_04')")
        with cur.copy(
            f"COPY {tabla} ({', '.join(cols + ['origen'])}) FROM STDIN WITH (FORMAT csv)"
        ) as copy:
            copy.write(buf.read())
        cur.execute(f"SELECT origen, count(*) FROM {tabla} GROUP BY origen")
        for fila in cur.fetchall():
            print(f"  {tabla} [{fila[0]}]: {fila[1]:,}")
    conn.commit()


SUPABASE_URL         = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

REST_BATCH = 500  # filas por request


def load_via_rest(pred: pl.DataFrame, shap: pl.DataFrame) -> None:
    """Fallback: carga via REST API (supabase-py) cuando no hay SUPABASE_DB_URL."""
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase-py: pip install supabase")

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        sys.exit("Faltan SUPABASE_URL / SUPABASE_SERVICE_KEY en backend/.env")

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Borra TODO artefacto previo (seed_dev y notebook_04), no solo seed_dev: el upsert
    # por PK no elimina features obsoletas si el set cambia entre versiones del modelo
    # (p. ej. la feature 'mes' quedaba huérfana tras pasar a mes_sin/mes_cos).
    print("Eliminando artefactos previos (seed_dev + notebook_04)...")
    client.table("predicciones").delete().in_("origen", ["seed_dev", "notebook_04"]).execute()
    client.table("shap_values").delete().in_("origen", ["seed_dev", "notebook_04"]).execute()

    pred_rows = pred.with_columns(pl.lit("notebook_04").alias("origen")).to_dicts()
    total_pred = len(pred_rows)
    print(f"Insertando {total_pred:,} predicciones en batches de {REST_BATCH}...")
    for i in range(0, total_pred, REST_BATCH):
        client.table("predicciones").upsert(
            pred_rows[i:i + REST_BATCH],
            on_conflict="upz_cod,anio,mes",
        ).execute()
        print(f"  {min(i + REST_BATCH, total_pred):,}/{total_pred:,}", end="\r")
    print()

    shap_rows = shap.with_columns(pl.lit("notebook_04").alias("origen")).to_dicts()
    total_shap = len(shap_rows)
    print(f"Insertando {total_shap:,} shap_values en batches de {REST_BATCH}...")
    for i in range(0, total_shap, REST_BATCH):
        client.table("shap_values").upsert(
            shap_rows[i:i + REST_BATCH],
            on_conflict="upz_cod,anio,mes,feature",
        ).execute()
        print(f"  {min(i + REST_BATCH, total_shap):,}/{total_shap:,}", end="\r")
    print()

    # Reporte final
    resp_p = client.table("predicciones").select("origen", count="exact").limit(0).execute()
    resp_s = client.table("shap_values").select("origen", count="exact").limit(0).execute()
    print(f"predicciones [notebook_04]: {resp_p.count:,}")
    print(f"shap_values  [notebook_04]: {resp_s.count:,}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                     help="Carga el modelo aunque no pase el quality-gate de metricas.json")
    args = ap.parse_args()

    validar_metricas(args.force)

    for p in (PRED_PARQUET, SHAP_PARQUET):
        if not p.exists():
            sys.exit(f"No existe {p} — ejecuta primero: python scripts/train_model.py")

    pred = validar(pl.read_parquet(PRED_PARQUET), PRED_COLS, "predicciones")
    shap = validar(pl.read_parquet(SHAP_PARQUET), SHAP_COLS, "shap_values")

    if args.dry_run:
        print("dry-run OK -- esquemas validos, no se toco la DB")
        return

    db_url = os.environ.get("SUPABASE_DB_URL", "")

    if db_url:
        # Via psycopg (COPY rapido, preferido)
        try:
            import psycopg
        except ImportError:
            sys.exit("Falta psycopg: pip install 'psycopg[binary]'")
        with psycopg.connect(db_url) as conn:
            copy_in(conn, "predicciones", PRED_COLS, pred, "notebook_04")
            copy_in(conn, "shap_values", SHAP_COLS, shap, "notebook_04")
    else:
        # Via REST API (sin SUPABASE_DB_URL)
        print("[INFO] SUPABASE_DB_URL no encontrado — usando REST API (mas lento).")
        load_via_rest(pred, shap)

    print("Switch completado: el backend ahora sirve artefactos reales del modelo XGBoost.")


if __name__ == "__main__":
    main()
