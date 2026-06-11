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
# F1: DAI Delito de Alto Impacto — dataset agregado por LOCALIDAD (21 filas, conteos por año)
# NOTA: no hay datos individuales de delitos por evento en datos abiertos Bogotá.
# El ZIP descarga DAILoc.geojson (localidades con conteos por tipo y año 2018-2026).
URL_F1_ZIP = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "7b270013-42ca-436b-9c1e-3bcb7d280c6b/resource/"
    "aba0e25d-d407-45f4-9a98-327493b538bd/download/dai_geojson.zip"
)
# F2: UPZ shapefile — Catastro Bogota ArcGIS REST (112 poligonos, CODIGO_UPZ)
URL_F2_ARCGIS = (
    "https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/"
    "ordenamientoterritorial/unidadplaneamientozonal/MapServer/0/query"
)
# F4: Cuadrantes Policia — GeoJSON directo (resource_show devuelve URL directa)
URL_F4_GEOJSON = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "b555594d-203e-4d34-8d17-32b13f94168b/resource/"
    "f0ad2ee3-bfd0-4825-9b31-bff9041649fa/download/cuadrantepolicia.geojson"
)
RESOURCE_ID_F5  = "30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef"  # NUSE 123 (Datastore)
DATASET_ID_F6   = "4rxi-8m8d"                              # Hurto Personas (Socrata)
URL_F7_GEOJSON  = (
    "https://datosabiertos.bogota.gov.co/dataset/"
    "55467552-0af4-4524-a390-a2956035744e/resource/"
    "29f2d770-bd5d-4450-9e95-8737167ba12f/download/manzanaestratificacion.json"
)
# F8: TransMilenio — ArcGIS REST de Transmilenio S.A.
URL_F8_ARCGIS = (
    "https://gis.transmilenio.gov.co/arcgis/rest/services/"
    "Troncal/consulta_estaciones_troncales/MapServer/0/query"
)

# F9: Secretaría Distrital de Seguridad — Boletines PDF mensuales
# AVISO (jun-2026): el contenido migró al Observatorio OSCJ (ArcGIS Experience Builder).
# La nueva URL carga 100% vía JavaScript — BeautifulSoup no puede scrapearlo.
# Descarga manual o Playwright requeridos. Ver scripts/index_corpus.py --seed-demo para demo.
URL_F9_SCJ_BASE = "https://oaiee.scj.gov.co/ObservatorioSCJ.html"
URL_F9_SCJ_OLD = "https://scj.gov.co/cifras/boletines"  # redirige al Observatorio
# F10: RSS feeds de noticias Bogotá (seguridad ciudadana)
RSS_FEEDS_F10 = {
    "el_tiempo": "https://www.eltiempo.com/rss/bogota.xml",
    "el_espectador": "https://feeds.elespectador.com/elespectador/justicia",
}
KEYWORDS_SEGURIDAD = [
    "hurto", "robo", "homicidio", "crimen", "delito", "seguridad",
    "policia", "captura", "detenido", "violencia", "extorsion",
    "secuestro", "lesiones", "atraco", "inseguridad", "cuadrante",
]
RAW_BOLETINES = RAW_DIR / "boletines_scj"

CKAN_BASE = "https://datosabiertos.bogota.gov.co/api/3/action"

# Open-Meteo — coordenadas Bogotá
BOG_LAT  = 4.6097
BOG_LON  = -74.0817
CLIMA_VARS = ["temperature_2m", "precipitation", "windspeed_10m", "weathercode"]

# ─── Validaciones por fuente ──────────────────────────────────────────────────
VALIDATIONS: dict[str, dict] = {
    # F1 es dataset AGREGADO por localidad (21 filas): 20 localidades + total Bogota.
    # Contiene conteos anuales por tipo de delito, NO registros individuales.
    # Variable objetivo real: usar F5 NUSE filtrado a tipos de crimen.
    "f1_delitos":         {"min_rows": 10},
    "f2_upz":             {"expected_rows": 112, "tolerance": 10},
    "f3_clima":           {"required_cols": ["time", "temperature_2m", "precipitation"]},
    "f4_cuadrantes":      {"min_rows": 500},
    "f5_nuse":            {"required_cols": ["ANIO", "MES", "COD_UPZ"], "min_rows": 500_000},
    "f6_hurto":           {"required_cols": ["fecha_hecho", "municipio"], "min_rows": 1_000},
    # F7: columna se llama ESTRATO (mayusculas) en el JSON de Catastro Bogota
    "f7_estratificacion": {"required_cols": ["ESTRATO"], "min_rows": 10_000},
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
    F2 — UPZ Shapefile IDECA (112 poligonos, CODIGO_UPZ, NOMBRE, AREA_HECTAREAS).
    Fuente: Catastro Bogota ArcGIS REST service (unidadplaneamientozonal MapServer).
    Estrategia: estatico — solo descarga si el archivo no existe o se fuerza.
    """
    source = "f2_upz"
    out_path = RAW_DIR / "f2_upz.geojson"
    saved = state.get(source)

    if not force and out_path.exists() and saved.get("row_count", 0) >= 100:
        rows = saved.get("row_count", 112)
        return ExtractResult(source, "skipped", 0, rows, str(out_path),
                             "UPZ shapefile ya descargado (estatico IDECA)")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             "[DRY-RUN] descargaria 112 UPZ desde Catastro ArcGIS REST")

    try:
        import requests
        import geopandas as gpd
        import json

        if verbose:
            print(f"    Descargando 112 UPZs desde Catastro ArcGIS REST...")
        resp = requests.get(URL_F2_ARCGIS, params={
            "where": "1=1",
            "outFields": "CODIGO_UPZ,NOMBRE,AREA_HECTAREAS",
            "f": "geojson",
            "resultRecordCount": 1000,
            "resultOffset": 0,
        }, timeout=60)
        resp.raise_for_status()
        geojson_data = resp.json()

        out_path.write_text(json.dumps(geojson_data), encoding="utf-8")
        gdf = gpd.read_file(out_path)

        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validacion fallo: {msg}")

        rows = len(gdf)
        if verbose:
            print(f"    {rows} UPZs descargados | CRS: {gdf.crs}")
        state.update(source, row_count=rows, file_path=str(out_path), status="ok")
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
    F4 — Cuadrantes de Policia MEBOG (GeoJSON directo, ~4800+ cuadrantes).
    Fuente: datosabiertos.bogota.gov.co resource GeoJSON directo.
    Estrategia: HTTP Last-Modified.
    """
    from src.etl import get_last_modified

    source = "f4_cuadrantes"
    out_path = RAW_DIR / "f4_cuadrantes.geojson"
    saved = state.get(source)

    server_lm = get_last_modified(URL_F4_GEOJSON)

    if not force and out_path.exists():
        if server_lm and server_lm == saved.get("last_modified_server"):
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "cuadrantes sin cambios en servidor")
        if not server_lm and out_path.exists():
            rows = saved.get("row_count", 0)
            return ExtractResult(source, "skipped", 0, rows, str(out_path),
                                 "servidor no devuelve Last-Modified — sin cambios")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaria GeoJSON cuadrantes (Last-Modified: {server_lm})")

    try:
        import requests
        import geopandas as gpd

        if verbose:
            print(f"    Descargando GeoJSON cuadrantes desde {URL_F4_GEOJSON[:70]}...")
        resp = requests.get(URL_F4_GEOJSON, timeout=180, stream=True)
        resp.raise_for_status()

        # Descargar con progreso
        total = int(resp.headers.get("Content-Length", 0))
        chunks = []
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=65_536):
            chunks.append(chunk)
            downloaded += len(chunk)
            if verbose and total:
                print(f"\r    {100*downloaded//total:3d}% ({downloaded/1e6:.1f} MB)", end="", flush=True)
        if verbose:
            print()

        content = b"".join(chunks)
        out_path.write_bytes(content)

        gdf = gpd.read_file(out_path)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validacion fallo: {msg}")

        rows = len(gdf)
        if verbose:
            print(f"    {rows:,} cuadrantes | columnas: {gdf.columns.tolist()}")
        state.update(source, last_modified_server=server_lm,
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
    F8 — Estaciones Troncales TransMilenio (puntos, ~140 estaciones).
    Fuente: ArcGIS REST de Transmilenio S.A. (consulta_estaciones_troncales).
    Estrategia: estatico — solo descarga si el archivo no existe o se fuerza.
    """
    import requests
    import json

    source = "f8_transmilenio"
    out_path = RAW_DIR / "f8_transmilenio.geojson"
    saved = state.get(source)

    if not force and out_path.exists() and saved.get("row_count", 0) >= 50:
        rows = saved.get("row_count", 0)
        return ExtractResult(source, "skipped", 0, rows, str(out_path),
                             "TransMilenio ya descargado (estatico ArcGIS REST)")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             "[DRY-RUN] descargaria estaciones TM desde ArcGIS REST")

    try:
        import geopandas as gpd

        if verbose:
            print(f"    Descargando estaciones TM desde ArcGIS REST...")
        resp = requests.get(URL_F8_ARCGIS, params={
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "resultRecordCount": 1000,
            "resultOffset": 0,
        }, timeout=60)
        resp.raise_for_status()

        geojson_data = resp.json()
        out_path.write_text(json.dumps(geojson_data), encoding="utf-8")

        gdf = gpd.read_file(out_path)
        ok, msg = _validate(source, gdf, verbose)
        if not ok:
            return ExtractResult(source, "error", 0, 0, "", f"Validacion fallo: {msg}")

        rows = len(gdf)
        if verbose:
            print(f"    {rows} estaciones TM | columnas: {gdf.columns.tolist()}")
        state.update(source, row_count=rows, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", rows, rows, str(out_path), msg)
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f9_scj_boletines(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F9 — PDFs de boletines mensuales SCJ (Secretaria Distrital de Seguridad y Convivencia).
    AVISO (jun-2026): los boletines migraron al Observatorio OSCJ que usa ArcGIS Experience
    Builder (100% JavaScript). BeautifulSoup no puede obtener los PDFs. Se necesita Playwright
    o descarga manual. Mientras tanto usar --seed-demo en index_corpus.py para el corpus demo.
    Fuente actual: https://oaiee.scj.gov.co/ObservatorioSCJ.html
    Salida: datos/raw/boletines_scj/*.pdf (un PDF por boletin)
    """
    import requests
    from bs4 import BeautifulSoup

    source = "f9_scj_boletines"
    RAW_BOLETINES.mkdir(parents=True, exist_ok=True)
    saved = state.get(source)

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(RAW_BOLETINES),
                             "[DRY-RUN] F9 requiere Playwright (ArcGIS JS). Usar --seed-demo en index_corpus.py")

    try:
        if verbose:
            print(f"    Accediendo a {URL_F9_SCJ_BASE}...")
            print(f"    AVISO: el Observatorio OSCJ usa ArcGIS JS — PDF scraping no disponible sin Playwright")
        resp = requests.get(URL_F9_SCJ_BASE, timeout=30,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # Buscar todos los enlaces a PDFs con "boletin" o "informe" en el nombre
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower() and any(
                kw in href.lower() for kw in ["boletin", "informe", "estadis"]
            ):
                if not href.startswith("http"):
                    href = "https://scj.gov.co" + href
                pdf_links.append(href)

        # Eliminar duplicados preservando orden
        seen = set()
        pdf_links = [x for x in pdf_links if not (x in seen or seen.add(x))]

        if not pdf_links:
            msg = ("F9: 0 PDFs encontrados. El Observatorio OSCJ usa ArcGIS JS (no scrappeable "
                   "con BS4). Descarga manual en: https://oaiee.scj.gov.co/ObservatorioSCJ.html "
                   "Seccion: Boletines > Estudios. O usa: python scripts/index_corpus.py --seed-demo")
            return ExtractResult(source, "error", 0, 0, str(RAW_BOLETINES), msg)

        if verbose:
            print(f"    Encontrados {len(pdf_links)} PDFs en la pagina SCJ")

        new_count = 0
        for url in pdf_links:
            fname = url.split("/")[-1].split("?")[0]
            if not fname.endswith(".pdf"):
                fname = fname + ".pdf"
            out = RAW_BOLETINES / fname
            if not out.exists() or force:
                try:
                    r = requests.get(url, timeout=60,
                                     headers={"User-Agent": "Mozilla/5.0"})
                    r.raise_for_status()
                    out.write_bytes(r.content)
                    new_count += 1
                    if verbose:
                        print(f"    Descargado: {fname}")
                except Exception as e:
                    if verbose:
                        print(f"    Error descargando {fname}: {e}")

        total_pdfs = len(list(RAW_BOLETINES.glob("*.pdf")))
        state.update(source, last_downloaded=str(date.today()),
                     row_count=total_pdfs, file_path=str(RAW_BOLETINES), status="ok")
        return ExtractResult(source, "updated", new_count, total_pdfs,
                             str(RAW_BOLETINES),
                             f"{new_count} PDFs nuevos | {total_pdfs} total en {RAW_BOLETINES.name}/")
    except Exception as exc:
        return ExtractResult(source, "error", 0, 0, "", str(exc))


def extract_f10_noticias_rss(
    state: PipelineState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> ExtractResult:
    """
    F10 — RSS feeds de noticias de Bogota filtrados por keywords de seguridad.
    Fuentes: El Tiempo Bogota + El Espectador Justicia
    Estrategia: append incremental — solo articulos nuevos desde ultima descarga.
    Salida: datos/raw/noticias_rss.jsonl (1 articulo JSON por linea)
    """
    import feedparser
    import json
    from datetime import datetime

    source = "f10_noticias_rss"
    out_path = RAW_DIR / "noticias_rss.jsonl"
    saved = state.get(source)
    last_downloaded = saved.get("last_downloaded", "2024-01-01")

    if dry_run:
        return ExtractResult(source, "updated", -1, -1, str(out_path),
                             f"[DRY-RUN] descargaria RSS feeds de El Tiempo y Espectador")

    try:
        # Leer articulos existentes para deduplicar
        existing_links = set()
        if out_path.exists() and not force:
            with open(out_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        art = json.loads(line)
                        existing_links.add(art.get("link", ""))
                    except Exception:
                        pass

        nuevos = []
        for feed_name, feed_url in RSS_FEEDS_F10.items():
            try:
                if verbose:
                    print(f"    Leyendo RSS: {feed_name}...")
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    link = getattr(entry, "link", "")
                    if link in existing_links:
                        continue
                    titulo = getattr(entry, "title", "")
                    resumen = getattr(entry, "summary", "")
                    texto = f"{titulo} {resumen}".lower()
                    # Filtrar solo noticias de seguridad
                    if not any(kw in texto for kw in KEYWORDS_SEGURIDAD):
                        continue
                    art = {
                        "fuente": feed_name,
                        "titulo": titulo,
                        "link": link,
                        "resumen": resumen,
                        "published": getattr(entry, "published", ""),
                        "descargado": str(date.today()),
                    }
                    nuevos.append(art)
                    existing_links.add(link)
            except Exception as e:
                if verbose:
                    print(f"    Error en feed {feed_name}: {e}")

        if nuevos:
            with open(out_path, "a", encoding="utf-8") as f:
                for art in nuevos:
                    f.write(json.dumps(art, ensure_ascii=False) + "\n")

        total = len(existing_links)
        state.update(source, last_downloaded=str(date.today()),
                     row_count=total, file_path=str(out_path), status="ok")
        return ExtractResult(source, "updated", len(nuevos), total, str(out_path),
                             f"{len(nuevos)} articulos nuevos | {total} total en noticias_rss.jsonl")
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
    "f9": extract_f9_scj_boletines,
    "f10": extract_f10_noticias_rss,
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
    "f9": "Boletines SCJ (PDF)",
    "f10": "Noticias RSS Bogota",
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
    # normalizar: "f1_delitos" → "f1", "f10_noticias" → "f10"
    # Buscar la clave mas larga de EXTRACTORS que sea prefijo del token dado
    def _normalize_key(k: str) -> str:
        if k in EXTRACTORS:
            return k
        # intentar match por prefijo (ej. "f10_noticias" -> "f10")
        for ek in sorted(EXTRACTORS.keys(), key=len, reverse=True):
            if k.startswith(ek):
                return ek
        return k
    keys = [_normalize_key(k) for k in keys]
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
        help="fuentes a procesar (f1..f10). Sin este flag -> todas",
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
