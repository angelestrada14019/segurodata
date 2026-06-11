# -*- coding: utf-8 -*-
"""Seed completo de Supabase para SeguroData.

Requiere SUPABASE_DB_URL en .env (Dashboard -> Settings -> Database -> Connection
string, session pooler). Idempotente: las filas sinteticas llevan origen='seed_dev'
y se borran antes de regenerar.

Uso:
    python scripts/seed_supabase.py                 # todo
    python scripts/seed_supabase.py --solo silver   # solo bulk silver (COPY)
    python scripts/seed_supabase.py --solo geo      # solo geometrias F2/F4
    python scripts/seed_supabase.py --solo synth    # solo predicciones+shap sinteticos

Nota: el seed inicial (jun 2026) se aplico via MCP Supabase sin geometrias.
Este script es la version reproducible y ademas carga las geometrias reales.
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
load_dotenv(ROOT / ".env")

DB_URL = os.environ.get("SUPABASE_DB_URL", "")

SILVER = ROOT / "datos" / "procesados" / "silver_upz_mes.parquet"
F2_GEOJSON = ROOT / "datos" / "raw" / "f2_upz.geojson"
F4_GEOJSON = ROOT / "datos" / "raw" / "f4_cuadrantes.geojson"

SILVER_COLS = [
    "upz_cod", "anio", "mes", "tipo_crimen", "es_crimen", "n_delitos",
    "n_delitos_upz_4sem", "n_delitos_upz_8sem", "cod_localidad", "nom_localidad",
    "temperatura_c", "precipitacion_mm_mes", "n_incidentes_nuse",
    "ratio_tipo_nuse_total", "estrato_promedio_upz", "cuadrantes_por_km2",
    "area_upz_km2", "n_estaciones_tm", "dist_tm_metros", "es_mitad_anio",
]


def conectar():
    try:
        import psycopg
    except ImportError:
        sys.exit("Falta psycopg: pip install 'psycopg[binary]'")
    if not DB_URL:
        sys.exit("Falta SUPABASE_DB_URL en .env (connection string del session pooler)")
    return psycopg.connect(DB_URL)


def seed_silver(conn) -> None:
    """Carga las 111,606 filas del Silver via COPY (segundos, no minutos)."""
    df = pl.read_parquet(SILVER).select(SILVER_COLS)
    # Codigos UPZ canon: 3 digitos con cero a la izquierda (igual que F2/F4)
    df = df.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.zfill(3))
    buf = io.BytesIO()
    df.write_csv(buf)
    buf.seek(0)
    buf.readline()  # saltar header
    with conn.cursor() as cur:
        cur.execute("TRUNCATE silver_upz_mes")
        with cur.copy(
            f"COPY silver_upz_mes ({', '.join(SILVER_COLS)}) FROM STDIN WITH (FORMAT csv)"
        ) as copy:
            copy.write(buf.read())
        cur.execute("SELECT count(*) FROM silver_upz_mes")
        n = cur.fetchone()[0]
    conn.commit()
    print(f"silver_upz_mes: {n:,} filas")


def seed_geometrias(conn) -> None:
    """Geometrias reales F2 (UPZ) y F4 (cuadrantes) + mapeo upz_codes por interseccion."""
    import geopandas as gpd

    gdf_upz = gpd.read_file(F2_GEOJSON).to_crs(4326)
    cod_col = next(c for c in gdf_upz.columns if c.upper() in ("CODIGO_UPZ", "UPZ_COD", "COD_UPZ"))
    nom_col = next(c for c in gdf_upz.columns if c.upper() in ("NOMBRE", "NOM_UPZ", "UPZ_NOMBRE"))
    gdf_upz["_cod"] = gdf_upz[cod_col].astype(str).str.zfill(3)

    with conn.cursor() as cur:
        for _, row in gdf_upz.iterrows():
            geom = row.geometry
            if geom.geom_type == "Polygon":
                from shapely.geometry import MultiPolygon
                geom = MultiPolygon([geom])
            cur.execute(
                """INSERT INTO upz_geometrias (upz_cod, upz_nombre, geom)
                   VALUES (%s, %s, ST_Multi(ST_GeomFromText(%s, 4326)))
                   ON CONFLICT (upz_cod) DO UPDATE
                   SET geom = EXCLUDED.geom, upz_nombre = EXCLUDED.upz_nombre""",
                (row["_cod"], str(row[nom_col]), geom.wkt),
            )
    conn.commit()
    print(f"upz_geometrias: {len(gdf_upz)} geometrias actualizadas")

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
    with conn.cursor() as cur:
        for cid, row in agg.iterrows():
            geom = geom_por_id.loc[cid]
            if hasattr(geom, "iloc"):
                geom = geom.iloc[0]
            cur.execute(
                """INSERT INTO cuadrantes_geom (cuadrante_id, nom_cai, telefono, upz_codes, geom)
                   VALUES (%s, %s, %s, %s, ST_Multi(ST_GeomFromText(%s, 4326)))
                   ON CONFLICT (cuadrante_id) DO UPDATE
                   SET geom = EXCLUDED.geom, upz_codes = EXCLUDED.upz_codes,
                       nom_cai = EXCLUDED.nom_cai, telefono = EXCLUDED.telefono""",
                (str(cid), str(row["nom_cai"]), str(row["telefono"]), row["upz_codes"], geom.wkt),
            )
    conn.commit()
    print(f"cuadrantes_geom: {len(agg)} cuadrantes actualizados")


SYNTH_SQL = """
DELETE FROM shap_values WHERE origen = 'seed_dev';
DELETE FROM predicciones WHERE origen = 'seed_dev';

WITH crimen AS (
  SELECT upz_cod, anio, mes, sum(n_delitos) AS n
  FROM silver_upz_mes WHERE es_crimen GROUP BY 1, 2, 3
),
s AS (
  SELECT g.upz_cod, coalesce(avg(c.n), 1.0) AS media
  FROM upz_geometrias g LEFT JOIN crimen c ON c.upz_cod = g.upz_cod
  GROUP BY g.upz_cod
),
months AS (
  SELECT 2025 AS anio, m AS mes FROM generate_series(7, 12) m
  UNION ALL SELECT 2026, m FROM generate_series(1, 12) m
),
base AS (
  SELECT s.upz_cod, mo.anio, mo.mes,
         s.media * (0.8 + 0.4 * (abs(hashtext(s.upz_cod || '-' || mo.anio || '-' || mo.mes)) % 1000) / 1000.0) AS score
  FROM s CROSS JOIN months mo
),
ranked AS (SELECT *, percent_rank() OVER (PARTITION BY anio, mes ORDER BY score) AS pr FROM base),
probs AS (
  SELECT upz_cod, anio, mes, pr,
    exp(-power(pr - 0.975, 2) / (2 * power(0.13, 2))) AS wc,
    exp(-power(pr - 0.850, 2) / (2 * power(0.13, 2))) AS wa,
    exp(-power(pr - 0.575, 2) / (2 * power(0.16, 2))) AS wm,
    exp(-power(pr - 0.200, 2) / (2 * power(0.20, 2))) AS wb
  FROM ranked
)
INSERT INTO predicciones (upz_cod, anio, mes, nivel_riesgo, prob_critico, prob_alto, prob_medio, prob_bajo, origen)
SELECT upz_cod, anio, mes,
  CASE WHEN pr >= 0.95 THEN 'CRITICO' WHEN pr >= 0.75 THEN 'ALTO'
       WHEN pr >= 0.40 THEN 'MEDIO' ELSE 'BAJO' END,
  wc / (wc + wa + wm + wb), wa / (wc + wa + wm + wb),
  wm / (wc + wa + wm + wb), wb / (wc + wa + wm + wb), 'seed_dev'
FROM probs;

WITH feats(feature, sesgo) AS (VALUES
  ('n_delitos_upz_4sem', 0.18), ('cuadrantes_por_km2', 0.12),
  ('estrato_promedio_upz', 0.06), ('luminarias_led_upz', 0.08),
  ('n_camaras_upz', 0.05), ('ratio_nuse_criminal_upz', 0.07),
  ('temperatura_c', 0.02), ('dist_tm_metros', 0.03)
),
r AS (
  SELECT upz_cod, anio, mes,
    CASE nivel_riesgo WHEN 'CRITICO' THEN 1.0 WHEN 'ALTO' THEN 0.7
         WHEN 'MEDIO' THEN 0.4 ELSE 0.2 END AS amp
  FROM predicciones WHERE origen = 'seed_dev'
)
INSERT INTO shap_values (upz_cod, anio, mes, feature, valor, origen)
SELECT r.upz_cod, r.anio, r.mes, f.feature,
  round((((abs(hashtext(r.upz_cod || r.anio::text || r.mes::text || f.feature)) % 2000) / 1000.0 - 1.0)
    * r.amp * 0.35 + f.sesgo * r.amp)::numeric, 4),
  'seed_dev'
FROM r CROSS JOIN feats f;
"""


def seed_sinteticos(conn) -> None:
    """Predicciones + SHAP sinteticos desde percentiles del Silver (origen='seed_dev')."""
    with conn.cursor() as cur:
        cur.execute(SYNTH_SQL)
        cur.execute("SELECT count(*) FROM predicciones WHERE origen = 'seed_dev'")
        np_ = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM shap_values WHERE origen = 'seed_dev'")
        ns = cur.fetchone()[0]
        cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        size = cur.fetchone()[0]
    conn.commit()
    print(f"predicciones seed_dev: {np_:,} | shap seed_dev: {ns:,} | DB: {size}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["silver", "geo", "synth"], default=None)
    args = ap.parse_args()
    with conectar() as conn:
        if args.solo in (None, "silver"):
            seed_silver(conn)
        if args.solo in (None, "geo"):
            seed_geometrias(conn)
        if args.solo in (None, "synth"):
            seed_sinteticos(conn)
    print("Seed completo.")


if __name__ == "__main__":
    main()
