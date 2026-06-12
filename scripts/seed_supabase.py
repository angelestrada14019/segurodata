# -*- coding: utf-8 -*-
"""Seed completo de Supabase para SeguroData.

Usa SUPABASE_URL + SUPABASE_SERVICE_KEY (REST API). Sin SUPABASE_DB_URL.
Idempotente: las filas sintéticas llevan origen='seed_dev'.

Uso:
    python scripts/seed_supabase.py                 # todo
    python scripts/seed_supabase.py --solo silver   # solo bulk silver
    python scripts/seed_supabase.py --solo geo      # solo geometrias F2/F4
    python scripts/seed_supabase.py --solo synth    # solo predicciones+shap sintéticos
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import polars as pl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    sys.exit("Faltan SUPABASE_URL y SUPABASE_SERVICE_KEY en backend/.env")

SILVER    = ROOT / "datos" / "procesados" / "silver_upz_mes.parquet"
F2_GEOJSON = ROOT / "datos" / "raw" / "f2_upz.geojson"
F4_GEOJSON = ROOT / "datos" / "raw" / "f4_cuadrantes.geojson"

SILVER_COLS = [
    "upz_cod", "anio", "mes", "tipo_crimen", "es_crimen", "n_delitos",
    "n_delitos_upz_4sem", "n_delitos_upz_8sem", "cod_localidad", "nom_localidad",
    "temperatura_c", "precipitacion_mm_mes", "n_incidentes_nuse",
    "ratio_tipo_nuse_total", "estrato_promedio_upz", "cuadrantes_por_km2",
    "area_upz_km2", "n_estaciones_tm", "dist_tm_metros", "es_mitad_anio",
]

BATCH = 500  # filas por request (~500 KB/batch con 20 cols)


def get_client():
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase-py: pip install supabase")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def seed_silver(client) -> None:
    """Carga las 111,606 filas del Silver via REST API en batches de 500."""
    if not SILVER.exists():
        sys.exit(f"No existe {SILVER} — corre src/transform.py primero")

    df = pl.read_parquet(SILVER).select(SILVER_COLS)
    df = df.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.zfill(3))

    print("Truncando silver_upz_mes...")
    client.rpc("truncate_silver", {}).execute()

    rows = df.to_dicts()
    total = len(rows)
    print(f"Insertando {total:,} filas en batches de {BATCH}...")

    for i in range(0, total, BATCH):
        client.table("silver_upz_mes").insert(rows[i:i + BATCH]).execute()
        print(f"  {min(i + BATCH, total):,}/{total:,}", end="\r")

    resp = client.table("silver_upz_mes").select("id", count="exact").limit(0).execute()
    print(f"\nsilver_upz_mes: {resp.count:,} filas")


def seed_geometrias(client) -> None:
    """Geometrias reales F2 (UPZ) y F4 (cuadrantes) via RPC con WKT."""
    try:
        import geopandas as gpd
        from shapely.geometry import MultiPolygon
    except ImportError:
        sys.exit("Falta geopandas: pip install geopandas")

    if not F2_GEOJSON.exists():
        sys.exit(f"No existe {F2_GEOJSON} — corre src/pipeline.py --source f2 primero")

    gdf_upz = gpd.read_file(F2_GEOJSON).to_crs(4326)
    cod_col = next(c for c in gdf_upz.columns if c.upper() in ("CODIGO_UPZ", "UPZ_COD", "COD_UPZ"))
    nom_col = next(c for c in gdf_upz.columns if c.upper() in ("NOMBRE", "NOM_UPZ", "UPZ_NOMBRE"))
    gdf_upz["_cod"] = gdf_upz[cod_col].astype(str).str.zfill(3)

    print(f"Cargando {len(gdf_upz)} UPZs via RPC...")
    for _, row in gdf_upz.iterrows():
        geom = row.geometry
        if geom.geom_type == "Polygon":
            geom = MultiPolygon([geom])
        client.rpc("upsert_upz_geom", {
            "p_upz_cod":    row["_cod"],
            "p_upz_nombre": str(row[nom_col]),
            "p_wkt":        geom.wkt,
        }).execute()
    print(f"upz_geometrias: {len(gdf_upz)} geometrias actualizadas")

    if not F4_GEOJSON.exists():
        print(f"Advertencia: {F4_GEOJSON} no existe — saltando cuadrantes")
        return

    gdf_cuad = gpd.read_file(F4_GEOJSON).to_crs(4326)
    join = gpd.sjoin(
        gdf_cuad[["PCUCODIGO", "PCUNOMCAI", "PCUTELEFON", "geometry"]],
        gdf_upz[["_cod", "geometry"]],
        how="left", predicate="intersects",
    )
    agg = join.groupby("PCUCODIGO").agg(
        nom_cai=("PCUNOMCAI", "first"),
        telefono=("PCUTELEFON", "first"),
        upz_codes=("_cod", lambda s: sorted({x for x in s if isinstance(x, str)})),
    )
    geom_por_id = gdf_cuad.set_index("PCUCODIGO").geometry

    print(f"Cargando {len(agg)} cuadrantes via RPC...")
    for cid, row in agg.iterrows():
        geom = geom_por_id.loc[cid]
        if hasattr(geom, "iloc"):
            geom = geom.iloc[0]
        if geom.geom_type == "Polygon":
            geom = MultiPolygon([geom])
        client.rpc("upsert_cuadrante_geom", {
            "p_cuadrante_id": str(cid),
            "p_nom_cai":      str(row["nom_cai"]),
            "p_telefono":     str(row["telefono"]),
            "p_upz_codes":    list(row["upz_codes"]),
            "p_wkt":          geom.wkt,
        }).execute()
    print(f"cuadrantes_geom: {len(agg)} cuadrantes actualizados")


def seed_sinteticos(client) -> None:
    """Predicciones + SHAP sintéticos via RPC regenerate_seed_dev (lógica en DB)."""
    print("Regenerando seed_dev via RPC...")
    resp = client.rpc("regenerate_seed_dev", {}).execute()
    data = resp.data or {}
    print(f"predicciones seed_dev: {data.get('predicciones', '?')} | shap_dev: {data.get('shap_values', '?')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["silver", "geo", "synth"], default=None)
    args = ap.parse_args()
    client = get_client()
    if args.solo in (None, "silver"):
        seed_silver(client)
    if args.solo in (None, "geo"):
        seed_geometrias(client)
    if args.solo in (None, "synth"):
        seed_sinteticos(client)
    print("Seed completo.")


if __name__ == "__main__":
    main()
