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
import os
import sys
from pathlib import Path

import polars as pl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PRED_PARQUET = ROOT / "datos" / "modelos" / "predicciones.parquet"
SHAP_PARQUET = ROOT / "datos" / "modelos" / "shap_values.parquet"

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


def copy_in(conn, tabla: str, cols: list[str], df: pl.DataFrame, origen: str) -> None:
    df = df.with_columns(pl.lit(origen).alias("origen"))
    buf = io.BytesIO()
    df.write_csv(buf)
    buf.seek(0)
    buf.readline()
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {tabla} WHERE origen = 'seed_dev'")
        with cur.copy(
            f"COPY {tabla} ({', '.join(cols + ['origen'])}) FROM STDIN WITH (FORMAT csv)"
        ) as copy:
            copy.write(buf.read())
        cur.execute(f"SELECT origen, count(*) FROM {tabla} GROUP BY origen")
        for fila in cur.fetchall():
            print(f"  {tabla} [{fila[0]}]: {fila[1]:,}")
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for p in (PRED_PARQUET, SHAP_PARQUET):
        if not p.exists():
            sys.exit(f"No existe {p} — genera los artefactos en el Notebook 04 primero")

    pred = validar(pl.read_parquet(PRED_PARQUET), PRED_COLS, "predicciones")
    shap = validar(pl.read_parquet(SHAP_PARQUET), SHAP_COLS, "shap_values")

    if args.dry_run:
        print("dry-run OK — esquemas validos, no se toco la DB")
        return

    try:
        import psycopg
    except ImportError:
        sys.exit("Falta psycopg: pip install 'psycopg[binary]'")
    db_url = os.environ.get("SUPABASE_DB_URL", "")
    if not db_url:
        sys.exit("Falta SUPABASE_DB_URL en .env")

    with psycopg.connect(db_url) as conn:
        copy_in(conn, "predicciones", PRED_COLS, pred, "notebook_04")
        copy_in(conn, "shap_values", SHAP_COLS, shap, "notebook_04")
    print("Switch completado: el backend ahora sirve artefactos reales del Notebook 04.")


if __name__ == "__main__":
    main()
