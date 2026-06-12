# -*- coding: utf-8 -*-
"""Detección de cambios estructurales en serie DAI 2018-2026 con ruptures PELT.

Fuente: datos/procesados/delitos_localidad_anio.parquet (F1 — Delito de Alto Impacto)
Salida: tabla change_points en Supabase (DELETE + INSERT — idempotente)

Algoritmo: Pelt (model='l2', min_size=2). Con 9 puntos anuales 2018-2026
una penalidad pen=3 detecta 1-3 cambios por localidad. Aumentar pen si
aparecen demasiados breakpoints espurios.

Eventos históricos esperados (validación manual):
  - 2020: BAJA en todas las localidades (COVID lockdown)
  - 2021: ALZA en algunas (reactivación + paro nacional mayo)
  - 2016-2017: posible BAJA en localidades periféricas (acuerdo de paz)

Uso:
    python scripts/compute_change_points.py
    python scripts/compute_change_points.py --dry-run        # imprime sin insertar
    python scripts/compute_change_points.py --pen 5          # penalidad más alta
    python scripts/compute_change_points.py --max-bp 2       # máx 2 breakpoints/localidad
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")
load_dotenv(ROOT / ".env")

PARQUET = ROOT / "datos" / "procesados" / "delitos_localidad_anio.parquet"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def get_client():
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase-py: pip install supabase")
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        sys.exit("Faltan SUPABASE_URL y SUPABASE_SERVICE_KEY en backend/.env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def pelt_localidad(signal: np.ndarray, anios: list[int], pen: float, max_bp: int) -> list[int]:
    """Corre PELT y devuelve índices de breakpoints (sin el punto final)."""
    try:
        import ruptures as rpt
    except ImportError:
        sys.exit("Falta ruptures: pip install ruptures")

    if len(signal) < 4:
        return []

    algo = rpt.Pelt(model="l2", min_size=2, jump=1)
    algo.fit(signal.reshape(-1, 1))
    bps = algo.predict(pen=pen)
    # ruptures siempre incluye n (último índice) — lo excluimos
    bps = [b for b in bps if 0 < b < len(signal)]
    # limitar al máximo configurado
    if len(bps) > max_bp:
        # conservar los de mayor magnitud de cambio
        mags = [abs(np.mean(signal[b:]) - np.mean(signal[:b])) for b in bps]
        bps = [bps[i] for i in sorted(range(len(bps)), key=lambda i: mags[i], reverse=True)[:max_bp]]
        bps.sort()
    return bps


def compute_all(df: pl.DataFrame, pen: float, max_bp: int) -> list[dict]:
    """Devuelve lista de dicts para insertar en change_points."""
    # Agregar a total_delitos por localidad × anio (suma todos los tipos DAI)
    agg = (
        df.group_by(["cod_localidad", "nom_localidad", "anio"])
        .agg(pl.col("n_delitos").sum().alias("total"))
        .sort(["cod_localidad", "anio"])
    )

    EXCLUIR = {"sin localización", "sin localizacion", "sin localiz"}

    rows = []
    for cod in agg["cod_localidad"].unique().to_list():
        sub = agg.filter(pl.col("cod_localidad") == cod).sort("anio")
        nom = str(sub["nom_localidad"][0])
        if nom.lower().strip() in EXCLUIR or nom.lower().startswith("sin local"):
            continue
        anios = sub["anio"].to_list()
        signal = sub["total"].to_numpy().astype(float)

        bps = pelt_localidad(signal, anios, pen, max_bp)
        for bp in bps:
            before = float(np.mean(signal[:bp]))
            after = float(np.mean(signal[bp:]))

            if before == 0:
                tipo, magnitude = "INDEFINIDO", 0.0
            else:
                magnitude = (after - before) / before
                tipo = "ALZA" if magnitude > 0.05 else ("BAJA" if magnitude < -0.05 else "INDEFINIDO")

            anio_ruptura = int(anios[bp]) if bp < len(anios) else int(anios[-1])
            rows.append({
                "localidad_cod": str(cod),
                "localidad_nom": nom,
                "fecha_ruptura": str(date(anio_ruptura, 1, 1)),
                "tipo_cambio": tipo,
                "magnitude": round(magnitude, 4),
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="imprime resultados sin insertar")
    ap.add_argument("--pen", type=float, default=3.0,
                    help="Penalidad PELT (default 3). Subir si hay demasiados breakpoints.")
    ap.add_argument("--max-bp", type=int, default=3,
                    help="Máximo breakpoints por localidad (default 3)")
    args = ap.parse_args()

    if not PARQUET.exists():
        sys.exit(f"No existe {PARQUET} — corre: python src/pipeline.py --source f1")

    df = pl.read_parquet(PARQUET)
    print(f"F1 DAI cargado: {len(df):,} filas | columnas: {df.columns}")
    print(f"Localidades: {df['cod_localidad'].n_unique()} | años: {sorted(df['anio'].unique().to_list())}")

    rows = compute_all(df, pen=args.pen, max_bp=args.max_bp)
    print(f"\nChange points detectados: {len(rows)} (pen={args.pen}, max_bp={args.max_bp})")
    print()

    # Imprimir resumen
    for r in sorted(rows, key=lambda x: abs(x["magnitude"]), reverse=True):
        sym = "+" if r["tipo_cambio"] == "ALZA" else ("-" if r["tipo_cambio"] == "BAJA" else "~")
        print(f"  {sym} {r['localidad_nom']:30s} {r['fecha_ruptura'][:4]}  "
              f"{r['tipo_cambio']:10s}  mag={r['magnitude']:+.2f}")

    if args.dry_run:
        print("\n[DRY-RUN] No se insertó nada en Supabase.")
        return

    if not rows:
        print("Sin change points — nada que insertar.")
        return

    print("\nInsertando en Supabase change_points...")
    client = get_client()

    # DELETE todas las filas existentes (re-seed idempotente)
    client.table("change_points").delete().gte("id", 0).execute()
    client.table("change_points").insert(rows).execute()

    resp = client.table("change_points").select("id", count="exact").limit(0).execute()
    print(f"change_points: {resp.count} filas cargadas en Supabase OK")

    # Validación rápida: COVID 2020 debe ser BAJA
    resp2 = client.table("change_points").select("*").eq("fecha_ruptura", "2020-01-01").execute()
    n_covid = len(resp2.data)
    if n_covid > 0:
        tipos = [r["tipo_cambio"] for r in resp2.data]
        print(f"Validacion COVID 2020: {n_covid} localidades, tipos: {set(tipos)}")
        if "BAJA" in tipos:
            print("  [OK] BAJA por lockdown COVID detectada")
        else:
            print(f"  [!] No se detecto BAJA en 2020 - revisar penalidad (pen={args.pen})")


if __name__ == "__main__":
    main()
