"""
ETL para el proyecto de predicción de crimen en Bogotá.

4 conectores:
  - CKAN       → datosabiertos.bogota.gov.co  (NUSE 123, geometrías, catastro)
  - Socrata    → www.datos.gov.co             (Policía Nacional, Medicina Legal)
  - ArcGIS REST→ datos.movilidadbogota.gov.co (siniestros, cámaras, sensores)
  - Open-Meteo → archive-api.open-meteo.com   (clima histórico Bogotá)

Uso:
  from src.etl import ckan_query_all, socrata_query, arcgis_query, open_meteo
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests
import polars as pl
from dotenv import load_dotenv

load_dotenv()
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

# ─────────────────────────────────────────────────────────────────────────────
# CKAN  (datosabiertos.bogota.gov.co)
# Plataforma: CKAN 2.x — API en /api/3/action/
# ─────────────────────────────────────────────────────────────────────────────

CKAN_BASE = "https://datosabiertos.bogota.gov.co/api/3/action"


def ckan_query(
    resource_id: str,
    filters: Optional[dict] = None,
    limit: int = 10_000,
    offset: int = 0,
) -> list[dict]:
    """
    Consulta paginada sobre CKAN Datastore — no descarga el archivo completo.

    Útil para NUSE 123: filtrar por COD_UPZ sin descargar el millón de filas.
    El formato COD_UPZ es "UPZ" + número sin ceros (ej. Chapinero = "UPZ99").

    Ejemplo:
        registros = ckan_query("30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef",
                               filters={"COD_UPZ": "UPZ99"})
    """
    params: dict = {"resource_id": resource_id, "limit": limit, "offset": offset}
    if filters:
        # CKAN espera el dict de filtros como JSON string en el campo "filters"
        params["filters"] = json.dumps(filters)
    resp = requests.get(f"{CKAN_BASE}/datastore_search", params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if not data["success"]:
        raise RuntimeError(f"CKAN error: {data.get('error')}")
    return data["result"]["records"]


def ckan_query_all(
    resource_id: str,
    filters: Optional[dict] = None,
    page_size: int = 10_000,
) -> pl.DataFrame:
    """Descarga paginada completa de un recurso CKAN. Devuelve Polars DataFrame."""
    records: list[dict] = []
    offset = 0
    while True:
        batch = ckan_query(resource_id, filters=filters, limit=page_size, offset=offset)
        if not batch:
            break
        records.extend(batch)
        offset += page_size
        if len(batch) < page_size:
            break
    return pl.from_dicts(records) if records else pl.DataFrame()


def ckan_download(url: str, local_path: str | Path) -> Path:
    """
    Descarga un archivo CKAN (GeoJSON, SHP ZIP, XLSX, GPKG) a disco.
    Crea el directorio padre si no existe.
    """
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8_192):
                f.write(chunk)
    return local_path


# ─────────────────────────────────────────────────────────────────────────────
# Socrata  (www.datos.gov.co)
# Plataforma: Socrata SODA API — sin token el límite es 1000 filas/request.
# Registrar token gratis en dev.socrata.com y guardar en .env como SOCRATA_APP_TOKEN.
# ─────────────────────────────────────────────────────────────────────────────


def socrata_query(
    dataset_id: str,
    host: str = "www.datos.gov.co",
    where: Optional[str] = None,
    select: Optional[str] = None,
    order: Optional[str] = None,
    app_token: Optional[str] = None,
    page_size: int = 50_000,
) -> pl.DataFrame:
    """
    Descarga paginada completa via Socrata SODA API.

    Ejemplos:
        # Homicidios nacionales
        df = socrata_query("m8fd-ahd9")

        # Lesiones no fatales Medicina Legal — solo Bogotá
        df = socrata_query("79dd-d24f", where="localidad_del_hecho IS NOT NULL")

        # Incautaciones solo Bogotá
        df = socrata_query("kk69-w2jj", where="municipio='BOGOTA D.C.'")
    """
    token = app_token or SOCRATA_APP_TOKEN
    base_url = f"https://{host}/resource/{dataset_id}.json"
    headers = {"X-App-Token": token} if token else {}
    records: list[dict] = []
    offset = 0
    while True:
        params: dict = {"$limit": page_size, "$offset": offset}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        if order:
            params["$order"] = order
        resp = requests.get(base_url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        records.extend(batch)
        offset += page_size
        if len(batch) < page_size:
            break
    return pl.from_dicts(records) if records else pl.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# ArcGIS REST  (datos.movilidadbogota.gov.co / Catastro Bogotá)
# Plataforma: ArcGIS Server MapServer/FeatureServer — paginación via resultOffset.
# ─────────────────────────────────────────────────────────────────────────────


def arcgis_query(  # noqa: C901
    service_url: str,
    layer_id: int = 0,
    where: str = "1=1",
    out_fields: str = "*",
    result_record_count: int = 1_000,
) -> "gpd.GeoDataFrame":
    """
    Consulta ArcGIS REST MapServer/FeatureServer con paginación automática.

    service_url: URL base del servicio (sin el /<layer_id>/query al final).

    Ejemplos:
        # Sensores de aforo (capas 1 y 2)
        sensores = arcgis_query(
            "https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/movilidad/controltransito/MapServer",
            layer_id=1
        )

        # Siniestros viales SDM (FeatureServer)
        siniestros = arcgis_query(
            "https://datos.movilidadbogota.gov.co/server/rest/services/.../FeatureServer",
            layer_id=0,
            where="ANIO >= 2020"
        )
    """
    import geopandas as gpd  # lazy import — solo se necesita cuando se llama esta función

    query_url = f"{service_url}/{layer_id}/query"
    all_features: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": "true",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": result_record_count,
        }
        resp = requests.get(query_url, params=params, timeout=60)
        resp.raise_for_status()
        geojson = resp.json()
        features = geojson.get("features", [])
        if not features:
            break
        all_features.extend(features)
        offset += result_record_count
        # ArcGIS marca explícitamente si hay más páginas
        if not geojson.get("exceededTransferLimit", False):
            break
    if not all_features:
        return gpd.GeoDataFrame()
    fc = {"type": "FeatureCollection", "features": all_features}
    return gpd.read_file(json.dumps(fc))


# ─────────────────────────────────────────────────────────────────────────────
# Open-Meteo  (clima histórico Bogotá)
# API gratuita sin clave. Histórico desde 1940 via archive-api.
# ─────────────────────────────────────────────────────────────────────────────

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


def open_meteo(
    lat: float,
    lon: float,
    start: str,
    end: str,
    variables: list[str],
    timezone: str = "America/Bogota",
    use_forecast_api: bool = False,
) -> pl.DataFrame:
    """
    Descarga datos climáticos de Open-Meteo.

    Para datos históricos (2020-2024) usar archive API (use_forecast_api=False).
    Para los últimos 16 días o pronóstico, usar use_forecast_api=True.

    Ejemplo:
        df = open_meteo(
            lat=4.6097, lon=-74.0817,
            start="2020-01-01", end="2024-12-31",
            variables=["temperature_2m", "precipitation", "windspeed_10m"]
        )
        # Columnas: time, temperature_2m, precipitation, windspeed_10m
    """
    base_url = OPEN_METEO_FORECAST if use_forecast_api else OPEN_METEO_ARCHIVE
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ",".join(variables),
        "timezone": timezone,
    }
    resp = requests.get(base_url, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    hourly = data.get("hourly", {})
    return pl.DataFrame(hourly)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def get_last_modified(url: str, timeout: int = 30) -> str | None:
    """
    HEAD request → retorna el header Last-Modified del servidor, o None si no existe.

    Úsalo antes de descargar un archivo para saber si cambió desde la última
    vez que lo descargamos. Compara contra el valor guardado en .pipeline_state.json.

    Ejemplo:
        lm = get_last_modified(URL_F1_ZIP)
        if lm != state.get("f1_delitos", {}).get("last_modified_server"):
            # archivo actualizado en el servidor → descargar
    """
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.headers.get("Last-Modified")
    except requests.RequestException:
        return None


def check_url(url: str, timeout: int = 30) -> tuple[int, float]:
    """
    Verifica si una URL responde con 2xx/3xx.
    Retorna (status_code, tiempo_respuesta_segundos).
    status_code = -1 si hay error de red.
    """
    try:
        t0 = time.time()
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code, round(time.time() - t0, 2)
    except requests.RequestException:
        return -1, -1.0
