# -*- coding: utf-8 -*-
"""Utilidades geoespaciales compartidas entre transform.py y scripts/seed_supabase.py."""

from __future__ import annotations

from pathlib import Path

import polars as pl


def build_upz_localidad_crosswalk(f5_parquet: Path) -> pl.DataFrame:
    """Mapeo upz_cod -> cod_localidad, nom_localidad, construido desde F5 (NUSE 123).

    F5 trae COD_UPZ/COD_LOCALIDAD/LOCALIDAD por cada incidente -- es la unica
    fuente del proyecto con ambos codigos juntos (el shapefile F2 de UPZ, IDECA,
    no tiene atributo de localidad -- confirmado contra el servicio ArcGIS real,
    el layer solo expone CODIGO_UPZ/NOMBRE/AREA_HECTAREAS/ZONA_ESTACIONAMIENTO/
    DECRETO_POT/ACTO_ADMINISTRATIVO).

    Algunas UPZ aparecen con mas de una localidad en F5 (imprecision de
    geocodificacion en el borde entre localidades) -- se resuelve tomando la
    localidad MAS FRECUENTE para esa UPZ (moda), no la primera fila que
    aparezca en el parquet, para que el resultado sea determinista.
    """
    f5_raw = pl.read_parquet(f5_parquet)

    return (
        f5_raw.select(["COD_UPZ", "COD_LOCALIDAD", "LOCALIDAD"])
        .with_columns(
            pl.col("COD_UPZ")
            .str.replace_all(r"[Uu][Pp][Zz]", "")
            .str.strip_chars()
            .alias("upz_cod"),
            pl.col("COD_LOCALIDAD").alias("cod_localidad"),
            pl.col("LOCALIDAD").alias("nom_localidad"),
        )
        .filter(~pl.col("COD_UPZ").str.contains("[Uu][Pp][Rr]"))
        .select(["upz_cod", "cod_localidad", "nom_localidad"])
        .group_by(["upz_cod", "cod_localidad", "nom_localidad"])
        .agg(pl.len().alias("_n"))
        .sort("_n", descending=True)
        .unique(subset=["upz_cod"], keep="first")
        .drop("_n")
    )
