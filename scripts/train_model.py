# -*- coding: utf-8 -*-
"""Pipeline Gold + XGBoost + SHAP para SeguroData Bogota.

Reemplaza NB03 + NB04 como script de produccion ejecutable sin Jupyter.
Los notebooks (si se crean) importan las funciones de este modulo y
solo muestran los outputs visuales.

Entradas:
  datos/procesados/silver_upz_mes.parquet   (111,606 filas x 20 cols)

Salidas:
  datos/features/tabla_maestra_upz.parquet  (1,918 filas x 14 features + target)
  datos/modelos/modelo_xgboost.pkl          (XGBClassifier serializado)
  datos/modelos/predicciones.parquet        (upz_cod, anio, mes, nivel_riesgo, prob_*)
  datos/modelos/shap_values.parquet         (upz_cod, anio, mes, feature, valor)

Uso:
    python scripts/train_model.py                   # ejecuta todo
    python scripts/train_model.py --dry-run         # Gold sin entrenar
    python scripts/train_model.py --verbose         # muestra metricas detalladas
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import polars as pl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / ".env")

SILVER  = ROOT / "datos" / "procesados" / "silver_upz_mes.parquet"
GOLD    = ROOT / "datos" / "features"  / "tabla_maestra_upz.parquet"
MODEL   = ROOT / "datos" / "modelos"   / "modelo_xgboost.pkl"
PRED    = ROOT / "datos" / "modelos"   / "predicciones.parquet"
SHAP_P  = ROOT / "datos" / "modelos"   / "shap_values.parquet"
METRICS = ROOT / "datos" / "modelos"   / "metricas.json"
F2_UPZ  = ROOT / "datos" / "raw"       / "f2_upz.geojson"

FEATURES = [
    # Históricas (lag temporal por UPZ)
    "n_delitos_upz_4sem",
    "n_delitos_upz_8sem",
    "n_delitos_upz_12sem",     # NUEVO — lag acumulado 3 meses
    "tendencia_upz",           # NUEVO — momentum mes a mes (lag1 - lag2)
    # Lag espacial (autocorrelación entre UPZs vecinas)
    "n_delitos_vecinos_lag",   # NUEVO — promedio de delitos de UPZs vecinas en t-1
    # Climáticas
    "temperatura_c",
    "precipitacion_mm_mes",
    # Espaciales / estáticas
    "estrato_promedio_upz",
    "cuadrantes_por_km2",
    "n_estaciones_tm",
    "dist_tm_metros",
    "ratio_nuse_criminal_upz",
    # Infraestructura (F11/F13/F14 — placeholder 0 hasta tener extractores)
    "km_via_intervenida_upz",
    "n_camaras_upz",
    "luminarias_led_upz",
    # Temporales cíclicas (reemplazan el `mes` crudo: dic y ene son adyacentes)
    "mes_sin",                 # NUEVO
    "mes_cos",                 # NUEVO
    "tipo_crimen_cod",
]

LABEL_MAP   = {"BAJO": 0, "MEDIO": 1, "ALTO": 2, "CRITICO": 3}
LABEL_INV   = {v: k for k, v in LABEL_MAP.items()}

# Split temporal: TRAIN = ene-oct 2025, TEST = nov 2025 en adelante
TRAIN_ANIO_MAX = 2025
TRAIN_MES_MAX  = 10


# ---------------------------------------------------------------------------
# FEATURE ENGINEERING (lag temporal extendido + lag espacial)
# ---------------------------------------------------------------------------

def _build_upz_adjacency() -> dict:
    """Adyacencia de UPZs por contigüidad ('touches') desde el shapefile F2.

    Devuelve {upz_cod: [vecinos]}. Si F2 no existe, devuelve dict vacío
    (el lag espacial cae a 0 sin romper el pipeline).
    """
    if not F2_UPZ.exists():
        return {}
    import geopandas as gpd

    gdf = gpd.read_file(F2_UPZ)
    code_col = "CODIGO_UPZ" if "CODIGO_UPZ" in gdf.columns else gdf.columns[0]
    gdf = gdf.to_crs("EPSG:3116")
    codes = gdf[code_col].astype(str).str.strip().tolist()
    adj: dict = {}
    for i, geom in enumerate(gdf.geometry):
        touch = gdf.geometry.touches(geom)
        adj[codes[i]] = [codes[j] for j in range(len(gdf)) if touch.iloc[j] and j != i]
    return adj


def _add_engineered_features(gold: pl.DataFrame, verbose: bool = False) -> pl.DataFrame:
    """Añade lag-3, tendencia (momentum), cíclicas de mes y lag espacial.

    Opera sobre la tabla agregada por UPZ x mes — requiere que ya existan
    n_delitos_total, n_delitos_upz_4sem y n_delitos_upz_8sem.
    """
    # índice mensual global para ordenar la serie por UPZ (maneja 2025-12 -> 2026-01)
    gold = gold.with_columns((pl.col("anio") * 12 + pl.col("mes")).alias("_t"))
    gold = gold.sort(["upz_cod", "_t"])

    gold = gold.with_columns([
        # lag acumulado 3 meses previos (familia 4sem/8sem/12sem)
        (pl.col("n_delitos_total").shift(1).over("upz_cod").fill_null(0)
         + pl.col("n_delitos_total").shift(2).over("upz_cod").fill_null(0)
         + pl.col("n_delitos_total").shift(3).over("upz_cod").fill_null(0)
         ).alias("n_delitos_upz_12sem"),
        # momentum: lag1 - lag2 = 4sem - (8sem - 4sem) = 2*4sem - 8sem
        (2 * pl.col("n_delitos_upz_4sem") - pl.col("n_delitos_upz_8sem"))
        .alias("tendencia_upz"),
        # codificación cíclica del mes (dic y ene quedan adyacentes)
        (2 * np.pi * pl.col("mes") / 12).sin().alias("mes_sin"),
        (2 * np.pi * pl.col("mes") / 12).cos().alias("mes_cos"),
    ])

    # ---- lag espacial: promedio de delitos de UPZs vecinas en t-1 ----
    adj = _build_upz_adjacency()
    if adj:
        pdf = gold.select([
            "upz_cod",
            pl.col("_t").alias("t"),
            "n_delitos_total",
        ]).to_pandas()
        pdf["upz_cod"] = pdf["upz_cod"].astype(str).str.strip()
        lookup = {(row.upz_cod, int(row.t)): float(row.n_delitos_total)
                  for row in pdf.itertuples(index=False)}
        vals = []
        for row in pdf.itertuples(index=False):
            vecinos = adj.get(row.upz_cod, [])
            prev = [lookup.get((v, int(row.t) - 1)) for v in vecinos]
            prev = [x for x in prev if x is not None]
            vals.append(float(np.mean(prev)) if prev else 0.0)
        gold = gold.with_columns(pl.Series("n_delitos_vecinos_lag", vals))
        if verbose:
            cob = sum(1 for v in vals if v > 0) / len(vals) * 100
            print(f"[Features] lag espacial: {len(adj)} UPZs con adyacencia | "
                  f"{cob:.0f}% filas con vecino-lag > 0")
    else:
        gold = gold.with_columns(pl.lit(0.0).alias("n_delitos_vecinos_lag"))
        if verbose:
            print("[Features] F2 no disponible — n_delitos_vecinos_lag = 0")

    return gold.drop("_t")


# ---------------------------------------------------------------------------
# 1. BUILD GOLD
# ---------------------------------------------------------------------------

def build_gold(verbose: bool = False) -> pl.DataFrame:
    """Lee Silver, filtra crimen, agrega por UPZ x mes, define nivel_riesgo."""
    if not SILVER.exists():
        sys.exit(f"No existe {SILVER} — corre: python src/transform.py")

    silver = pl.read_parquet(SILVER)
    if verbose:
        print(f"[Silver] {len(silver):,} filas | {silver['upz_cod'].n_unique()} UPZs")

    crimen = silver.filter(pl.col("es_crimen") == True)
    if verbose:
        print(f"[Crimen] {len(crimen):,} filas (es_crimen=True)")

    # ---- tipo dominante por upz x mes ----
    tipo_dom = (
        crimen
        .group_by(["upz_cod", "anio", "mes", "tipo_crimen"])
        .agg(pl.col("n_delitos").sum().alias("_cnt"))
        .sort(["upz_cod", "anio", "mes", "_cnt"], descending=[False, False, False, True])
        .group_by(["upz_cod", "anio", "mes"])
        .agg(pl.col("tipo_crimen").first().alias("tipo_delito_dominante"))
    )

    # ---- label encode tipo_crimen (categorico -> int) ----
    tipos_unicos = sorted(crimen["tipo_crimen"].unique().to_list())
    tipo_enc = {t: i for i, t in enumerate(tipos_unicos)}

    tipo_dom = tipo_dom.with_columns(
        pl.col("tipo_delito_dominante")
        .replace_strict(tipo_enc, return_dtype=pl.Int32, default=0)
        .alias("tipo_crimen_cod")
    )

    # ---- ratio NUSE criminal: delitos_crimen / n_incidentes_nuse ----
    nuse_ratio = (
        crimen
        .group_by(["upz_cod", "anio", "mes"])
        .agg([
            pl.col("n_delitos").sum().alias("n_delitos_total"),
            pl.col("n_delitos_upz_4sem").sum().alias("n_delitos_upz_4sem"),
            pl.col("n_delitos_upz_8sem").sum().alias("n_delitos_upz_8sem"),
            pl.col("n_incidentes_nuse").first(),
            pl.col("temperatura_c").first(),
            pl.col("precipitacion_mm_mes").first(),
            pl.col("estrato_promedio_upz").first(),
            pl.col("cuadrantes_por_km2").first(),
            pl.col("area_upz_km2").first(),
            pl.col("n_estaciones_tm").first(),
            pl.col("dist_tm_metros").first(),
        ])
        .with_columns(
            (pl.col("n_delitos_total")
             / pl.col("n_incidentes_nuse").clip(lower_bound=1))
            .alias("ratio_nuse_criminal_upz")
        )
    )

    # Unir tipo dominante
    gold = nuse_ratio.join(tipo_dom, on=["upz_cod", "anio", "mes"], how="left")

    # Placeholder F11/F13/F14 (extractores aun no implementados)
    gold = gold.with_columns([
        pl.lit(0.0).alias("km_via_intervenida_upz"),
        pl.lit(0).cast(pl.Int32).alias("n_camaras_upz"),
        pl.lit(0).cast(pl.Int32).alias("luminarias_led_upz"),
    ])

    # ---- nivel_riesgo por percentiles ----
    q95 = gold["n_delitos_total"].quantile(0.95)
    q75 = gold["n_delitos_total"].quantile(0.75)
    q40 = gold["n_delitos_total"].quantile(0.40)

    gold = gold.with_columns(
        pl.when(pl.col("n_delitos_total") >= q95).then(pl.lit("CRITICO"))
          .when(pl.col("n_delitos_total") >= q75).then(pl.lit("ALTO"))
          .when(pl.col("n_delitos_total") >= q40).then(pl.lit("MEDIO"))
          .otherwise(pl.lit("BAJO"))
          .alias("nivel_riesgo")
    )

    # ---- features de ingeniería: lag-3, tendencia, cíclicas, lag espacial ----
    gold = _add_engineered_features(gold, verbose=verbose)

    if verbose:
        dist = gold["nivel_riesgo"].value_counts().sort("nivel_riesgo")
        print(f"[Gold] {len(gold):,} filas | {len(gold.columns)} cols | "
              f"nivel_riesgo: {dist.to_dicts()}")
        print(f"  q40={q40:.0f} | q75={q75:.0f} | q95={q95:.0f}")

    GOLD.parent.mkdir(exist_ok=True)
    gold.write_parquet(GOLD)
    if verbose:
        print(f"[OK] Gold guardado: {GOLD}")

    return gold


# ---------------------------------------------------------------------------
# 2. TRAIN XGBOOST
# ---------------------------------------------------------------------------

def train_xgboost(gold: pl.DataFrame, verbose: bool = False):
    """Entrena XGBClassifier con split temporal estricto."""
    try:
        import xgboost as xgb
    except ImportError:
        sys.exit("Falta xgboost: pip install xgboost")

    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
    )

    df = gold.to_pandas()

    # Rellenar nulos: mediana para continuas, 0 para conteos/placeholder
    mediana_estrato = df["estrato_promedio_upz"].median()
    mediana_dist    = df["dist_tm_metros"].median()
    df["estrato_promedio_upz"] = df["estrato_promedio_upz"].fillna(mediana_estrato)
    df["dist_tm_metros"]       = df["dist_tm_metros"].fillna(mediana_dist)
    df["cuadrantes_por_km2"]   = df["cuadrantes_por_km2"].fillna(0.0)
    df["n_estaciones_tm"]      = df["n_estaciones_tm"].fillna(0)
    df["n_delitos_upz_4sem"]   = df["n_delitos_upz_4sem"].fillna(0)
    df["n_delitos_upz_8sem"]   = df["n_delitos_upz_8sem"].fillna(0)
    df["n_delitos_upz_12sem"]  = df["n_delitos_upz_12sem"].fillna(0)
    df["tendencia_upz"]        = df["tendencia_upz"].fillna(0)
    df["n_delitos_vecinos_lag"] = df["n_delitos_vecinos_lag"].fillna(0)
    df["tipo_crimen_cod"]      = df["tipo_crimen_cod"].fillna(0)

    df["y"] = df["nivel_riesgo"].map(LABEL_MAP).astype(int)

    # Split temporal estricto
    mask_train = (df["anio"] < TRAIN_ANIO_MAX) | (
        (df["anio"] == TRAIN_ANIO_MAX) & (df["mes"] <= TRAIN_MES_MAX)
    )
    train = df[mask_train].copy()
    test  = df[~mask_train].copy()

    if verbose:
        print(f"[Split] train={len(train):,} filas (hasta {TRAIN_ANIO_MAX}-{TRAIN_MES_MAX:02d}) | "
              f"test={len(test):,} filas")

    if len(test) == 0:
        print("[AVISO] No hay filas de test — el Silver solo cubre hasta oct-2025. "
              "Entrenando con todos los datos.")
        test = train.copy()

    X_train = train[FEATURES].astype(float)
    y_train = train["y"]
    X_test  = test[FEATURES].astype(float)
    y_test  = test["y"]

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        random_state=42,
        eval_metric="mlogloss",
        early_stopping_rounds=20,
        verbosity=0,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    preds_test  = model.predict(X_test)
    y_test_arr  = y_test.to_numpy()
    acc         = accuracy_score(y_test, preds_test)

    # ---- métricas ordinales (nivel_riesgo es BAJO<MEDIO<ALTO<CRITICO) ----
    # Accuracy dentro de ±1 banda: una predicción a una banda de distancia NO es
    # un fallo operativo (los cortes q40/q75/q95 son arbitrarios). MAE ordinal
    # mide "qué tan lejos" cae el error en unidades de banda.
    within1   = float((np.abs(preds_test - y_test_arr) <= 1).mean())
    mae_ord   = float(np.abs(preds_test - y_test_arr).mean())
    macro_f1  = float(f1_score(y_test, preds_test, average="macro"))
    cm        = confusion_matrix(y_test, preds_test, labels=[0, 1, 2, 3]).tolist()
    report    = classification_report(
        y_test, preds_test, labels=[0, 1, 2, 3],
        target_names=["BAJO", "MEDIO", "ALTO", "CRITICO"],
        output_dict=True, zero_division=0,
    )

    metricas = {
        "accuracy_exact":         round(acc, 4),
        "accuracy_within_1_band": round(within1, 4),
        "mae_ordinal":            round(mae_ord, 4),
        "macro_f1":               round(macro_f1, 4),
        "confusion_matrix":       cm,
        "confusion_labels":       ["BAJO", "MEDIO", "ALTO", "CRITICO"],
        "per_class": {
            k: {kk: round(vv, 4) for kk, vv in v.items()}
            for k, v in report.items()
            if k in ("BAJO", "MEDIO", "ALTO", "CRITICO")
        },
        "n_train":        int(len(X_train)),
        "n_test":         int(len(X_test)),
        "best_iteration": int(getattr(model, "best_iteration", 0) or 0),
        "n_features":     len(FEATURES),
        "split":          f"TRAIN<=2025-{TRAIN_MES_MAX:02d}, TEST=2025-{TRAIN_MES_MAX + 1:02d}+",
    }
    METRICS.parent.mkdir(exist_ok=True)
    METRICS.write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[Modelo] exact={acc:.3f} | dentro de ±1 banda={within1:.3f} | "
          f"macro-F1={macro_f1:.3f} | MAE ordinal={mae_ord:.3f}")

    if verbose:
        print(classification_report(
            y_test, preds_test, labels=[0, 1, 2, 3],
            target_names=["BAJO", "MEDIO", "ALTO", "CRITICO"], zero_division=0,
        ))
        print("[Matriz de confusión] filas=real, cols=pred (BAJO/MEDIO/ALTO/CRITICO):")
        for fila in cm:
            print(f"    {fila}")
        fi = dict(zip(FEATURES, model.feature_importances_))
        top = sorted(fi.items(), key=lambda x: x[1], reverse=True)
        print("[Importancia por feature (xgb.feature_importances_):]")
        for f, imp in top:
            bar = "#" * int(imp * 60)
            print(f"  {f:35s} {imp:.4f} {bar}")
    else:
        print(f"[Modelo] best_iteration={model.best_iteration}")

    print(f"[OK] Métricas guardadas: {METRICS}")
    MODEL.parent.mkdir(exist_ok=True)
    with open(MODEL, "wb") as fp:
        pickle.dump(model, fp)
    print(f"[OK] Modelo guardado: {MODEL}")

    return model, df, X_test, y_test


# ---------------------------------------------------------------------------
# 3. SHAP VALUES
# ---------------------------------------------------------------------------

def compute_shap(
    model,
    df,      # pandas DataFrame completo (todas las filas del Gold)
    verbose: bool = False,
) -> pl.DataFrame:
    """Calcula SHAP para cada fila del Gold y devuelve DataFrame largo."""
    try:
        import shap
    except ImportError:
        sys.exit("Falta shap: pip install shap")

    X_all = df[FEATURES].astype(float).fillna(0)

    explainer  = shap.TreeExplainer(model)
    shap_vals  = explainer.shap_values(X_all)

    # shap_vals puede ser lista[n_clases] de arrays (n_samples x n_features)
    # o array 3D (n_samples x n_features x n_classes) segun version
    if isinstance(shap_vals, np.ndarray) and shap_vals.ndim == 3:
        shap_by_class = [shap_vals[:, :, c] for c in range(shap_vals.shape[2])]
    else:
        shap_by_class = shap_vals  # lista de arrays

    preds_all = model.predict(X_all)

    rows = []
    for i, row in df.iterrows():
        pred_cls = int(preds_all[df.index.get_loc(i)] if hasattr(df.index, 'get_loc') else preds_all[i])
        sv = shap_by_class[pred_cls][i if not hasattr(df.index, 'get_loc') else df.index.get_loc(i)]
        for j, feat in enumerate(FEATURES):
            rows.append({
                "upz_cod": str(row["upz_cod"]).zfill(3),
                "anio":    int(row["anio"]),
                "mes":     int(row["mes"]),
                "feature": feat,
                "valor":   float(sv[j]),
            })

    shap_df = pl.DataFrame(rows, schema={
        "upz_cod": pl.Utf8,
        "anio":    pl.Int32,
        "mes":     pl.Int32,
        "feature": pl.Utf8,
        "valor":   pl.Float64,
    })

    if verbose:
        mean_abs = (
            shap_df.with_columns(pl.col("valor").abs())
            .group_by("feature")
            .agg(pl.col("valor").mean().alias("mean_abs_shap"))
            .sort("mean_abs_shap", descending=True)
        )
        print("[SHAP] Importancia media absoluta por feature:")
        for r in mean_abs.to_dicts():
            bar = "#" * int(r["mean_abs_shap"] * 200)
            print(f"  {r['feature']:35s} {r['mean_abs_shap']:.4f} {bar}")

    SHAP_P.parent.mkdir(exist_ok=True)
    shap_df.write_parquet(SHAP_P)
    print(f"[OK] SHAP guardado: {SHAP_P} ({len(shap_df):,} filas)")
    return shap_df


# ---------------------------------------------------------------------------
# 4. PREDICCIONES
# ---------------------------------------------------------------------------

def save_predicciones(model, df, verbose: bool = False) -> pl.DataFrame:
    """Genera predicciones para todas las filas del Gold."""
    X_all  = df[FEATURES].astype(float).fillna(0)
    probs  = model.predict_proba(X_all)
    preds  = model.predict(X_all)
    labels = [LABEL_INV[int(p)] for p in preds]

    pred_df = pl.DataFrame({
        "upz_cod":      [str(r).zfill(3) for r in df["upz_cod"].tolist()],
        "anio":         [int(x) for x in df["anio"].tolist()],
        "mes":          [int(x) for x in df["mes"].tolist()],
        "nivel_riesgo": labels,
        "prob_bajo":    probs[:, 0].tolist(),
        "prob_medio":   probs[:, 1].tolist(),
        "prob_alto":    probs[:, 2].tolist(),
        "prob_critico": probs[:, 3].tolist(),
    })

    if verbose:
        dist = pred_df["nivel_riesgo"].value_counts().sort("nivel_riesgo")
        print(f"[Predicciones] distribucion nivel_riesgo: {dist.to_dicts()}")

    PRED.parent.mkdir(exist_ok=True)
    pred_df.write_parquet(PRED)
    print(f"[OK] Predicciones guardadas: {PRED} ({len(pred_df):,} filas)")
    return pred_df


# ---------------------------------------------------------------------------
# 5. SESGO POR ESTRATO
# ---------------------------------------------------------------------------

def analisis_sesgo(pred_df: pl.DataFrame, gold: pl.DataFrame, verbose: bool = False) -> None:
    """Analiza si el modelo discrimina sistematicamente por estrato."""
    merged = pred_df.join(
        gold.select(["upz_cod", "anio", "mes", "estrato_promedio_upz"]),
        on=["upz_cod", "anio", "mes"],
        how="left",
    ).with_columns(
        pl.col("estrato_promedio_upz")
        .fill_null(3.0)
        .round(0)
        .cast(pl.Int32)
        .alias("estrato_bin")
    )

    print("\n[Sesgo] Distribucion nivel_riesgo por estrato:")
    for est in sorted(merged["estrato_bin"].unique().to_list()):
        sub = merged.filter(pl.col("estrato_bin") == est)
        total = len(sub)
        critico_pct = sub.filter(pl.col("nivel_riesgo") == "CRITICO").height / total * 100
        alto_pct    = sub.filter(pl.col("nivel_riesgo") == "ALTO").height / total * 100
        print(f"  Estrato {est}: n={total:4d} | CRITICO={critico_pct:5.1f}% | ALTO={alto_pct:5.1f}%")

    print("  -> Si CRITICO% en estrato 1-2 es >> estrato 5-6 SIN soporte en datos: revisar sesgo.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="SeguroData — pipeline Gold + XGBoost + SHAP")
    ap.add_argument("--dry-run",  action="store_true", help="solo construye Gold, no entrena")
    ap.add_argument("--verbose",  action="store_true", help="muestra metricas detalladas")
    ap.add_argument("--skip-shap", action="store_true", help="salta calculo SHAP (mas rapido)")
    args = ap.parse_args()

    print("=" * 60)
    print("  SeguroData — Gold + XGBoost + SHAP")
    print("=" * 60)

    # Paso 1: Gold
    print("\n[1/4] Construyendo tabla Gold...")
    gold = build_gold(verbose=args.verbose)

    if args.dry_run:
        print("\n[DRY-RUN] Gold construido. Saliendo sin entrenar.")
        return

    # Paso 2: Modelo
    print("\n[2/4] Entrenando XGBoost...")
    model, df, X_test, y_test = train_xgboost(gold, verbose=args.verbose)

    # Paso 3: Predicciones (todas las filas del Gold)
    print("\n[3/4] Generando predicciones para todas las UPZs...")
    pred_df = save_predicciones(model, df, verbose=args.verbose)

    # Paso 4: SHAP
    if not args.skip_shap:
        print("\n[4/4] Calculando SHAP values...")
        compute_shap(model, df, verbose=args.verbose)
    else:
        print("\n[4/4] SHAP saltado (--skip-shap)")

    # Analisis de sesgo
    if args.verbose:
        analisis_sesgo(pred_df, gold)

    print("\n" + "=" * 60)
    print("  COMPLETADO. Proximos pasos:")
    print("  1. python scripts/load_model_artifacts.py --dry-run")
    print("  2. python scripts/load_model_artifacts.py")
    print("     (requiere SUPABASE_DB_URL en backend/.env)")
    print("=" * 60)


if __name__ == "__main__":
    main()
