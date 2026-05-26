"""
pipeline.py — Extracción incremental de las 8 fuentes de SeguroData Bogotá.

Cada extractor compara el estado actual (fecha de descarga, Last-Modified, max(fecha))
contra lo guardado en datos/raw/.pipeline_state.json y SOLO descarga si hay
datos nuevos. Así una segunda ejecución el mismo día es instantánea.

Uso desde terminal:
    python src/pipeline.py                         # extrae todo (solo lo nuevo)
    python src/pipeline.py --status                # muestra estado sin descargar
    python src/pipeline.py --source f3             # solo Open-Meteo
    python src/pipeline.py --source f1 f5 f6       # múltiples fuentes
    python src/pipeline.py --source f1 --force     # fuerza re-descarga
    python src/pipeline.py --dry-run               # qué descargaría (sin hacerlo)
    python src/pipeline.py --verbose               # output detallado

Uso desde notebook/Colab:
    from src.pipeline import run_pipeline, extract_f3_clima
    resultados = run_pipeline()
    for r in resultados:
        print(r.source, r.status, r.rows_new, r.message)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

# ─── Rutas base ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Garantizar que el proyecto esté en sys.path para importar src.etl
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
RAW_DIR      = PROJECT_ROOT / "datos" / "raw"
STATE_FILE   = RAW_DIR / ".pipeline_state.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ─── URLs y resource IDs ──────────────────────────────────────────────────────
URL_F1_ZIP = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "7b270013-42ca-436b-9c1e-3bcb7d280c6b/resource/"
    "aba0e25d-d407-45f4-9a98-327493b538bd/download/dai_geojson.zip"
)
URL_F2_GEOJSON = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "808582fc-ffc8-4649-8428-7e1fd8d3820c/resource/"
    "a5c8c591-0708-420f-8eb7-9f3147e21c40/download/unidadplaneamientolocal.json"
)
RESOURCE_ID_F4  = "f0ad2ee3-bfd0-4825-9b31-bff9041649fa"  # Cuadrantes (descarga ZIP)
RESOURCE_ID_F5  = "30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef"  # NUSE 123 (Datastore)
DATASET_ID_F6   = "4rxi-8m8d"                              # Hurto Personas (Socrata)
URL_F7_GEOJSON  = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "55467552-0af4-4524-a390-a2956035744e/resource/"
    "29f2d770-bd5d-4450-9e95-8737167ba12f/download/manzanaestratificacion.json"
)
PACKAGE_ID_F8   = "9be8b6fb-8059-492f-a866-4a1ac031c502"  # TransMilenio (CKAN package)

CKAN_BASE = "https://datosabiertos.bogota.gov.co/api/3/action"

# Open-Meteo — coordenadas Bogotá
BOG_LAT  = 4.6097
BOG_LON  = -74.0817
CLIMA_VARS = ["temperature_2m", "precipitation", "windspeed_10m", "weathercode"]

# ─── Validaciones por fuente ──────────────────────────────────────────────────
VALIDATIONS: dict[str, dict] = {
    "f1_delitos":         {"required_cols": ["tipologia_delito", "fecha"], "min_rows": 400_000},
    "f2_upz":             {"expected_rows": 112, "tolerance": 10},
    "f3_clima":           {"required_cols": ["time", "temperature_2m", "precipitation"]},
    "f4_cuadrantes":      {"min_rows": 500},
    "f5_nuse":            {"required_cols": ["ANIO", "MES", "COD_UPZ"], "min_rows": 500_000},
    "f6_hurto":           {"required_cols": ["fecha_hecho", "municipio"], "min_rows": 1_000},
    "f7_estratificacion": {"required_cols": ["estrato"], "min_rows": 50_000},
    "f8_transmilenio":    {"min_rows": 50},
}


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class ExtractResult:
    source: str        # "f1_delitos", "f3_clima", etc.
    status: str        # "updated" | "skipped" | "error"
    rows_new: int      # filas nuevas descargadas (0 si skipped)
    rows_total: int    # total de filas en el archivo final
    file_path: str     # ruta al archivo guardado
    message: str       # descripción legible del resultado

    def __str__(self) -> str:
        icon = {"updated": "[OK]", "skipped": "[--]", "error": "[!!]"}.get(self.status, "[?]")
        return (
            f"{icon} {self.source:<22} {self.status:<8} "
            f"new={self.rows_new:>8,}  total={self.rows_total:>8,}  {self.message}"
        )


# ─── Estado persistente ───────────────────────────────────────────────────────

class PipelineState:
    """
    Lee y escribe datos/raw/.pipeline_state.json.
    Cada fuente guarda: last_downloaded, last_modified_server,
    max_date_in_data, row_count, file_path, status.
    """

    def __init__(self) -> None:
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        if STATE_FILE.exists():
            try:
                self._data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def save(self) -> None:
        STATE_FILE.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def get(self, source: str) -> dict:
        return self._data.get(source, {})

    def update(self, source: str, **kwargs) -> None:
        if source not in self._data:
            self._data[source] = {}
        self._data[source].update(kwargs)
        self.save()

    def all_sources(self) -> dict:
        return self._data


# ─── Helpers internos ─────────────────────────────────────────────────────────

def _validate(source: str, df_or_gdf, verbose: bool = False) -> tuple[bool, str]:
    """
    Aplica las validaciones de VALIDATIONS[source].
    Devuelve (ok, mensaje).
    """
    import polars as pl

    rules = VALIDATIONS.get(source, {})
    if not rules:
        return True, "sin reglas de validación"

    # número de filas
    try:
        n = len(df_or_gdf)
    except Exception:
        n = 0

    if "min_rows" in rules and n < rules["min_rows"]:
        return False, f"solo {n:,} filas — mínimo esperado {rules['min_rows']:,}"

    if "expected_rows" in rules:
        tolerance = rules.get("tolerance", 0)
        if abs(n - rules["expected_rows"]) > tolerance:
            return False, f"{n} filas — se esperaban {rules['expected_rows']} ± {tolerance}"

    # columnas requeridas
    if "required_cols" in rules:
        if hasattr(df_or_gdf, "columns"):
            actual_cols = list(df_or_gdf.columns)
        else:
            actual_cols = []
        missing = [c for c in rules["required_cols"] if c not in actual_cols]
        if missing:
            return False, f"columnas faltantes: {missing}"

    return True, f"{n:,} filas — validación OK"


def _gdf_to_parquet(gdf, path: Path) -> int:
    """Convierte GeoDataFrame → Polars → Parquet (geometry como WKT). Devuelve nº de filas."""
    import polars as pl

    gdf = gdf.copy()
    if "geometry" in gdf.columns:
        gdf["geometry_wkt"] = gdf.geometry.to_wkt()
        gdf = gdf.drop(columns="geometry")
    df = pl.from_pandas(gdf)
    df.write_parquet(path)
    return len(df)


def _get_ckan_resource_url(resource_id: str, timeout: int = 30) -> str | None:
    """Consulta resource_show de CKAN para obtener la URL de descarga."""
    import requests
    try:
        resp = requests.get(
            f"{CKAN_BASE}/resource_show",
            params={"id": resource_id},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data["result"].get("url")
    except Exception:
        pass
    return None


def _get_ckan_package_metadata_modified(package_id: str, timeout: int = 30) -> str | None:
    """Consulta package_show de CKAN para obtener metadata_modified."""
    import requests
    try:
        resp = requests.get(
            f"{CKAN_BASE}/package_show",
            params={"id": package_id},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data["result"].get("metadata_modified")
    except Exception:
        pass
    return None


def _download_zip_and_geojson(url: str, zip_path: Path, verbose: bool = False) -> "gpd.GeoDataFrame":
    """Descarga ZIP, extrae el primer .geojson/.json que encuentre, devuelve GeoDataFrame."""
    import requests
    import geopandas as gpd

    if verbose:
        print(f"    Descargando ZIP desde {url[:80]}…")

    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunks = []
        for chunk in resp.iter_content(chunk_size=65_536):
            chunks.append(chunk)
            downloaded += len(chunk)
            if verbose and total:
                pct = 100 * downloaded // total
                print(f"\r    {pct:3d}% ({downloaded/1e6:.1f} MB)", end="", flush=True)
        if verbose:
            print()
        content = b"".join(chunks)

    zip_path.write_bytes(content)

    with zipfile.ZipFile(io.BytesIO(content)) as z:
        names = z.namelist()
        geo_file = next(
            (n for n in names if n.lower().endswith(".geojson")),
            next((n for n in names if n.lower().endswith(".json")), None),
        )
        if geo_file is None:
            raise ValueError(f"No se encontró .geojson/.json en el ZIP. Archivos: {names}")
        if verbose:
            print(f"    Leyendo {geo_file} del ZIP…")
        gdf = gpd.read_file(z.open(geo_file))

    return gdf


# ─── 8 extractores ────────────────────────────────────────────────────────────

def extract_f1_delitos(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F1 — Delito de Alto Impacto (ZIP con GeoJSON, ~500K+ registros).
    Estrategia: HTTP Last-Modified → si más nuevo que el guardado → re-descarga.
    """
    from src.etl import get_last_modified

    source = "f1_delitos"
    out_path = RAW_DIR / "f1_delito_alto_impacto.parquet"
    zip_path = RAW_DIR / "f1_delito_alto_impacto.zip"

    saved = state.get(source)
    server_lm = get_last_modified(URL_F1_ZIP)

    if not force and out_path.exists():
        if server_lm and server_lm == saved.get("last_modified_server"):
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "Last-Modified sin cambios en el servidor")
        if not server_lm and out_path.exists():
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "servidor no devuelve Last-Modified — se asume sin cambios")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría ZIP desde servidor (Last-Modified: {server_lm})")

    try:
        gdf = _download_zip_and_geojson(URL_F1_ZIP, zip_path, verbose=verbose)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validación falló: {msg}")

        rows = _gdf_to_parquet(gdf, out_path)
        state.update(source, last_modified_server=server_lm, row_count=rows,
                     file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f2_upz(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F2 — UPZ Shapefile IDECA (GeoJSON directo, 112 polígonos, ~estático).
    Estrategia: HTTP Last-Modified.
    """
    from src.etl import get_last_modified

    source = "f2_upz"
    out_path = RAW_DIR / "f2_upz.geojson"

    saved = state.get(source)
    server_lm = get_last_modified(URL_F2_GEOJSON)

    if not force and out_path.exists():
        if server_lm and server_lm == saved.get("last_modified_server"):
            rows = saved.get("row_count", 112)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "UPZ shapefile sin cambios")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría GeoJSON UPZ (Last-Modified: {server_lm})")

    try:
        import requests
        import geopandas as gpd
        if verbose:
            print(f"    Descargando UPZ desde {URL_F2_GEOJSON[:70]}...")
        resp = requests.get(URL_F2_GEOJSON, timeout=120)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)

        gdf = gpd.read_file(out_path)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validación falló: {msg}")

        rows = len(gdf)
        state.update(source, last_modified_server=server_lm, row_count=rows,
                     file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f3_clima(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F3 — Open-Meteo clima horario Bogotá (2020 → hoy).
    Estrategia: append incremental desde max(time) en el Parquet existente.
    Open-Meteo tiene ~1 día de retraso → end = ayer.
    """
    from src.etl import open_meteo
    import polars as pl

    source = "f3_clima"
    out_path = RAW_DIR / "f3_clima_bogota.parquet"
    end_date = str(date.today() - timedelta(days=1))

    if out_path.exists() and not force:
        try:
            existing = pl.read_parquet(out_path)
            max_time = existing["time"].cast(pl.Utf8).max()
            max_date_str = str(max_time)[:10]
            start_date = str(date.fromisoformat(max_date_str) + timedelta(days=1))
        except Exception:
            existing = None
            start_date = "2020-01-01"
    else:
        existing = None
        start_date = "2020-01-01"

    if start_date > end_date:
        rows = len(pl.read_parquet(out_path)) if out_path.exists() else 0
        return ExtractResult(source, "skipped", 0, rows, str(out_path),
                             f"ya al día hasta {end_date}")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] append clima {start_date} -> {end_date}")

    try:
        if verbose:
            print(f"    Descargando clima {start_date} -> {end_date}...")
        new_data = open_meteo(BOG_LAT, BOG_LON, start_date, end_date, CLIMA_VARS)

        ok, msg = _validate(source, new_data, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validación falló: {msg}")

        rows_new = len(new_data)
        if existing is not None and rows_new > 0:
            combined = pl.concat([existing, new_data]).unique(subset=["time"]).sort("time")
        elif rows_new > 0:
            combined = new_data.sort("time")
        else:
            rows_total = len(existing) if existing is not None else 0
            return ExtractResult(source, "skipped", 0, rows_total, str(out_path),
                                 "Open-Meteo no devolvió filas nuevas")

        combined.write_parquet(out_path)
        rows_total = len(combined)
        state.update(source, max_date_in_data=end_date, row_count=rows_total,
                     file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows_new, rows_total, str(out_path),
                             f"append {start_date}->{end_date} | {msg}")
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f4_cuadrantes(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F4 — Cuadrantes de Policía MEBOG (ZIP con GeoJSON).
    Estrategia: consultar resource_show → URL → HTTP Last-Modified.
    """
    from src.etl import get_last_modified

    source = "f4_cuadrantes"
    out_path = RAW_DIR / "f4_cuadrantes.geojson"
    zip_path = RAW_DIR / "f4_cuadrantes.zip"

    saved = state.get(source)

    # Obtener URL de descarga desde CKAN
    url = saved.get("download_url") or _get_ckan_resource_url(RESOURCE_ID_F4)
    if not url:
        return ExtractResult(source, "error", 0, 0, "",
                             "No se pudo obtener URL de descarga de CKAN para F4")

    server_lm = get_last_modified(url)

    if not force and out_path.exists():
        if server_lm and server_lm == saved.get("last_modified_server"):
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "cuadrantes sin cambios en servidor")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría cuadrantes (Last-Modified: {server_lm})")

    try:
        import geopandas as gpd
        gdf = _download_zip_and_geojson(url, zip_path, verbose=verbose)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validacion fallo: {msg}")

        gdf.to_file(out_path, driver="GeoJSON")
        rows = len(gdf)
        state.update(source, download_url=url, last_modified_server=server_lm,
                     row_count=rows, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f5_nuse(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F5 — NUSE 123 incidentes C4 (CKAN Datastore, ~1M+ filas).
    Estrategia: CKAN no soporta >= en filtros, así que descargamos el año actual
    + el anterior y deduplicamos contra el Parquet existente.
    Columna temporal: ANIO (año) + MES.
    """
    from src.etl import ckan_query_all
    import polars as pl

    source = "f5_nuse"
    out_path = RAW_DIR / "f5_nuse_123.parquet"

    current_year = date.today().year
    years_to_fetch = [current_year - 1, current_year]

    if out_path.exists() and not force:
        try:
            existing = pl.read_parquet(out_path)
            max_anio = existing["ANIO"].cast(pl.Int32).max()
            if max_anio >= current_year:
                # ya tenemos el año actual → no descargar si fue hace menos de 7 días
                saved = state.get(source)
                from datetime import datetime
                last_dl = saved.get("last_downloaded", "2000-01-01")
                days_since = (date.today() - date.fromisoformat(last_dl[:10])).days
                if days_since < 7:
                    return ExtractResult(source, "skipped", 0, len(existing), str(out_path),
                                         f"descargado hace {days_since} días — OK para NUSE mensual")
        except Exception:
            existing = None
    else:
        existing = None

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría NUSE años {years_to_fetch}")

    try:
        new_records: list = []
        for yr in years_to_fetch:
            if verbose:
                print(f"    Descargando NUSE año {yr}…")
            batch = ckan_query_all(RESOURCE_ID_F5, filters={"ANIO": str(yr)})
            if len(batch) > 0:
                new_records.append(batch)

        if not new_records:
            rows = len(existing) if existing is not None else 0
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "NUSE: no se obtuvieron datos del servidor")

        new_df = pl.concat(new_records)
        ok, msg = _validate(source, new_df if existing is None else
                            pl.concat([existing, new_df]), verbose)

        dedup_cols = ["ANIO", "MES", "COD_UPZ"]
        available_dedup = [c for c in dedup_cols if c in new_df.columns]

        if existing is not None:
            combined = pl.concat([existing, new_df])
            if available_dedup:
                combined = combined.unique(subset=available_dedup)
            rows_new = len(combined) - len(existing)
        else:
            combined = new_df
            rows_new = len(combined)

        combined.write_parquet(out_path)
        rows_total = len(combined)

        from datetime import datetime
        state.update(source, last_downloaded=datetime.now().isoformat()[:10],
                     row_count=rows_total, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", max(rows_new, 0), rows_total,
                             str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f6_hurto(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F6 — Hurto a Personas Policía Nacional (Socrata 4rxi-8m8d).
    Estrategia: $where fecha_hecho > 'max_fecha' → solo filas nuevas.
    """
    from src.etl import socrata_query
    import polars as pl
    from datetime import datetime

    source = "f6_hurto"
    out_path = RAW_DIR / "f6_hurto_personas.parquet"

    saved = state.get(source)
    start_date = "2019-01-01"

    if out_path.exists() and not force:
        try:
            existing = pl.read_parquet(out_path)
            # buscar columna de fecha
            date_col = next(
                (c for c in existing.columns if "fecha" in c.lower()), None
            )
            if date_col:
                max_date = existing[date_col].cast(pl.Utf8).max()
                start_date = str(max_date)[:10]
                # si max_date es de hace menos de 7 días, saltar
                days_since = (date.today() - date.fromisoformat(start_date)).days
                if days_since < 7:
                    return ExtractResult(source, "skipped", 0, len(existing),
                                         str(out_path),
                                         f"actualizado hace {days_since} días — OK")
        except Exception:
            existing = None
    else:
        existing = None

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría Socrata F6 desde {start_date}")

    try:
        where_clause = f"fecha_hecho > '{start_date}T00:00:00.000'"
        if verbose:
            print(f"    Descargando Hurto Personas (Socrata) desde {start_date}…")
        new_df = socrata_query(
            DATASET_ID_F6,
            host="www.datos.gov.co",
            where=where_clause if existing is not None else None,
            order="fecha_hecho ASC",
        )

        if len(new_df) == 0:
            rows = len(existing) if existing is not None else 0
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "sin registros nuevos en Socrata")

        ok, msg = _validate(source, new_df, verbose)

        if existing is not None:
            combined = pl.concat([existing, new_df])
            # deduplicar si hay fecha_hecho + municipio
            dedup_cols = [c for c in ["fecha_hecho", "municipio", "cantidad"]
                          if c in combined.columns]
            if dedup_cols:
                combined = combined.unique(subset=dedup_cols[:2])
            rows_new = len(combined) - len(existing)
        else:
            combined = new_df
            rows_new = len(combined)

        combined.write_parquet(out_path)
        rows_total = len(combined)
        state.update(source, last_downloaded=datetime.now().isoformat()[:10],
                     row_count=rows_total, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", max(rows_new, 0), rows_total,
                             str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f7_estratificacion(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F7 — Estratificación por manzana SDP (~100K+ polígonos, archivo pesado ~200MB).
    Estrategia: HTTP Last-Modified → solo descarga si cambió.
    Streaming con progreso para no agotar RAM.
    """
    from src.etl import get_last_modified

    source = "f7_estratificacion"
    out_path = RAW_DIR / "f7_estratificacion.parquet"

    saved = state.get(source)
    server_lm = get_last_modified(URL_F7_GEOJSON)

    if not force and out_path.exists():
        if server_lm and server_lm == saved.get("last_modified_server"):
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "estratificacion sin cambios (archivo pesado)")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaria estratificacion ~200MB (Last-Modified: {server_lm})")

    try:
        import requests
        import geopandas as gpd
        if verbose:
            print("    Descargando estratificacion (~200MB) con streaming...")
        resp = requests.get(URL_F7_GEOJSON, stream=True, timeout=600)
        resp.raise_for_status()

        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunks = []
        for chunk in resp.iter_content(chunk_size=65_536):
            chunks.append(chunk)
            downloaded += len(chunk)
            if verbose and total:
                pct = 100 * downloaded // total
                print(f"\r    {pct:3d}% ({downloaded/1e6:.1f} MB)", end="", flush=True)
        if verbose:
            print()

        content = b"".join(chunks)
        if verbose:
            print("    Leyendo GeoJSON con GeoPandas…")
        gdf = gpd.read_file(io.BytesIO(content))

        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validación falló: {msg}")

        rows = _gdf_to_parquet(gdf, out_path)
        state.update(source, last_modified_server=server_lm, row_count=rows,
                     file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f8_transmilenio(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F8 — Estaciones TransMilenio (CKAN, GeoJSON de puntos, ~150 estaciones).
    Estrategia: package_show → metadata_modified → comparar contra estado.
    """
    import requests

    source = "f8_transmilenio"
    out_path = RAW_DIR / "f8_transmilenio.geojson"

    saved = state.get(source)

    # Consultar metadata_modified del package
    meta_modified = _get_ckan_package_metadata_modified(PACKAGE_ID_F8)

    if not force and out_path.exists():
        if meta_modified and meta_modified == saved.get("metadata_modified"):
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "TransMilenio sin cambios (metadata_modified igual)")

    # Obtener URL del recurso GeoJSON dentro del package
    url = saved.get("download_url")
    if not url:
        try:
            resp = requests.get(
                f"{CKAN_BASE}/package_show",
                params={"id": PACKAGE_ID_F8},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("success"):
                resources = data["result"].get("resources", [])
                # preferir recurso GeoJSON o JSON
                for r in resources:
                    fmt = (r.get("format") or "").lower()
                    if "geojson" in fmt or "json" in fmt:
                        url = r.get("url")
                        break
                if not url and resources:
                    url = resources[0].get("url")
        except Exception as exc:
            return ExtractResult(source, "error", 0, 0, "", f"No pudo obtener URL TM: {exc}")

    if not url:
        return ExtractResult(source, "error", 0, 0, "",
                             "No se encontró recurso descargable para F8 en CKAN")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaría TM GeoJSON (metadata_modified: {meta_modified})")

    try:
        import geopandas as gpd
        if verbose:
            print(f"    Descargando estaciones TransMilenio desde {url[:70]}...")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)

        gdf = gpd.read_file(out_path)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validacion fallo: {msg}")

        rows = len(gdf)
        state.update(source, download_url=url, metadata_modified=meta_modified,
                     row_count=rows, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


# ─── Mapa de extractores ──────────────────────────────────────────────────────

EXTRACTORS = {
    "f1": extract_f1_delitos,
    "f2": extract_f2_upz,
    "f3": extract_f3_clima,
    "f4": extract_f4_cuadrantes,
    "f5": extract_f5_nuse,
    "f6": extract_f6_hurto,
    "f7": extract_f7_estratificacion,
    "f8": extract_f8_transmilenio,
}

SOURCE_LABELS = {
    "f1": "Delito Alto Impacto",
    "f2": "UPZ Shapefile",
    "f3": "Clima Open-Meteo",
    "f4": "Cuadrantes Policía",
    "f5": "NUSE 123",
    "f6": "Hurto Personas (PN)",
    "f7": "Estratificación SDP",
    "f8": "Estaciones TM",
}


# ─── Orquestador ──────────────────────────────────────────────────────────────

def run_pipeline(
    sources: Optional[list[str]] = None,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[ExtractResult]:
    """
    Ejecuta el pipeline de extracción para las fuentes indicadas.

    sources: lista de claves ["f1", "f3", "f5"] o None para todas.
    force:   True → re-descarga aunque no haya cambios.
    dry_run: True → informa qué haría sin descargar nada.
    verbose: True → imprime progreso detallado.

    Retorna lista de ExtractResult. Excepciones individuales no detienen el pipeline.

    Ejemplo:
        from src.pipeline import run_pipeline
        results = run_pipeline(verbose=True)
        for r in results:
            print(r)
    """
    state = PipelineState()
    keys = sources if sources else list(EXTRACTORS.keys())
    # normalizar: "f1_delitos" → "f1"
    keys = [k[:2] if len(k) > 2 else k for k in keys]
    # filtrar claves válidas
    keys = [k for k in keys if k in EXTRACTORS]

    results: list[ExtractResult] = []
    for key in keys:
        fn = EXTRACTORS[key]
        if verbose:
            print(f"\n[{key.upper()}] {SOURCE_LABELS.get(key, key)}")
        result = fn(state, force=force, dry_run=dry_run, verbose=verbose)
        results.append(result)
        if not verbose:
            print(result)

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _print_status(state: PipelineState) -> None:
    """Imprime tabla de estado de todas las fuentes."""
    data = state.all_sources()
    print()
    print(f"{'Fuente':<22} {'Estado':<8} {'Filas':>10}  {'Ultima descarga':<20}  Archivo")
    print("-" * 90)
    for key in EXTRACTORS:
        # buscar entrada en el state file que empiece con esta clave (f1, f2…)
        info = next(
            (v for k, v in data.items() if k.startswith(key)),
            {}
        )
        status  = info.get("status", "pendiente")
        rows    = f"{info.get('row_count', 0):,}" if info.get("row_count") else "-"
        last_dl = (info.get("last_downloaded") or info.get("last_modified_server") or "-")[:19]
        fpath   = Path(info.get("file_path", "-")).name if info.get("file_path") else "-"
        label   = SOURCE_LABELS.get(key, key)
        print(f"{label:<22} {status:<8} {rows:>10}  {last_dl:<20}  {fpath}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="SeguroData — extracción incremental de fuentes de datos (Bronze layer)",
    )
    parser.add_argument(
        "--source", "-s",
        nargs="+",
        choices=list(EXTRACTORS.keys()),
        metavar="FX",
        help="fuentes a procesar (f1..f8). Sin este flag -> todas",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="forzar re-descarga aunque no haya cambios",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="muestra qué descargaría sin ejecutar",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="muestra estado de todas las fuentes y sale",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="output detallado con progreso de descarga",
    )
    args = parser.parse_args()

    if args.status:
        _print_status(PipelineState())
        return

    sep = "-" * 60
    print(f"\n{sep}")
    print("  SeguroData Bogota - Pipeline de extraccion (Bronze layer)")
    print(sep)
    if args.dry_run:
        print("  [DRY-RUN] - no se descargara nada\n")

    results = run_pipeline(
        sources=args.source,
        force=args.force,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    print(f"\n{sep}")
    updated = sum(1 for r in results if r.status == "updated")
    skipped = sum(1 for r in results if r.status == "skipped")
    errors  = sum(1 for r in results if r.status == "error")
    print(f"  Resumen: {updated} actualizadas  {skipped} sin cambios  {errors} errores")
    print(f"{sep}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
