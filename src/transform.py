"""
transform.py — Capa Silver: limpieza, agregacion y joins espaciales.

Toma los archivos Bronze de datos/raw/ y produce datos limpios
agregados por UPZ x mes en datos/procesados/.

Responsabilidad de esta capa:
  - Limpiar y normalizar campos (fechas, coordenadas, codigos UPZ)
  - Agregar eventos de crimen a nivel UPZ x mes
  - Calcular lag features historicos (4 semanas, 8 semanas)
  - Hacer spatial joins (estratificacion, cuadrantes, TransMilenio)
  - Calcular ratio NUSE / delitos por UPZ x mes
  - Unir todo en una sola tabla Silver

NO hace:
  - Seleccion de variables
  - Analisis de correlacion (eso es Gold / Notebook 03)
  - Normalizacion para el modelo (eso es Gold)
  - Definicion de la variable objetivo nivel_riesgo (eso es Gold)

Uso desde terminal:
    python src/transform.py                   # correr todos los pasos
    python src/transform.py --status          # ver estado sin ejecutar
    python src/transform.py --step f1         # un paso especifico
    python src/transform.py --step f1 f3 f5   # varios pasos
    python src/transform.py --step f7 --force # forzar re-calculo
    python src/transform.py --dry-run         # que haria sin ejecutar

Uso desde notebook:
    from src.transform import run_transform
    resultados = run_transform(verbose=True)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Rutas base ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RAW_DIR  = PROJECT_ROOT / "datos" / "raw"
PROC_DIR = PROJECT_ROOT / "datos" / "procesados"
STATE_FILE = PROC_DIR / ".transform_state.json"

PROC_DIR.mkdir(parents=True, exist_ok=True)

from src.geo_utils import build_upz_localidad_crosswalk  # noqa: E402

# ─── Columnas esperadas en Bronze ─────────────────────────────────────────────
# Nombres posibles para cada campo (el raw puede variar entre versiones del dataset)
# F2 UPZ shapefile (Catastro Bogota ArcGIS) usa "CODIGO_UPZ"
UPZ_COL_CANDIDATES  = ["CODIGO_UPZ", "codigo_upz", "upz", "UPZ", "cod_upz", "COD_UPZ",
                        "codigo", "CODIGO"]
TIPO_COL_CANDIDATES = ["tipologia_delito", "TIPOLOGIA_DELITO", "tipo_delito", "TIPO_DELITO",
                        "TIPO_DETALLE", "tipo_detalle"]
FECHA_COL_CANDIDATES = ["fecha", "FECHA", "fecha_hecho", "FECHA_HECHO"]
HORA_COL_CANDIDATES  = ["hora", "HORA", "hora_hecho", "HORA_HECHO"]
LAT_COL_CANDIDATES   = ["latitud", "LATITUD", "lat", "LAT", "latitude"]
LON_COL_CANDIDATES   = ["longitud", "LONGITUD", "lon", "LON", "longitude"]

# Bounding box Bogota D.C.
BOG_LAT_MIN, BOG_LAT_MAX = 3.7, 4.9
BOG_LON_MIN, BOG_LON_MAX = -74.4, -73.9

# Franja horaria
FRANJAS = {
    "madrugada": (0, 5),
    "manana":    (6, 11),
    "tarde":     (12, 17),
    "noche":     (18, 23),
}

# Tipos NUSE que representan delitos de alto impacto
CRIME_TYPES_NUSE = {
    "HURTO EFECTUADO",
    "HURTO EN PROCESO",
    "LESIONES PERSONALES",
    "NARCÓTICOS",           # NARCÓTICOS
    "RIÑA",                  # RIÑA
    "MALTRATO",
    "VIOLENCIA SEXUAL",
    "SECUESTRO",
    "DISPAROS",
    "PORTE DE ARMAS",
    "PANDILLAS",
    "RAPTO",
    "INTENTO O VIOLACIÓN DE DOMICILIO",  # INTENTO O VIOLACIÓN DE DOMICILIO
    "ACCIÓN SUBVERSIVA",     # ACCIÓN SUBVERSIVA
    "DELINCUENTE CAPTURADO POR CIVIL",
    "EXHIBICIONES O ACTOS OBSCENOS",
    "HALLAZGO DE EXPLOSIVOS",
    "EXPLOSIÓN",             # EXPLOSIÓN
    "FUGA DE PRESOS",
}

# Prefijos de columna en F1 (DAI Delito Alto Impacto) -> tipo de delito
F1_TIPO_MAP = {
    "CMH":   "Homicidio",
    "CMLP":  "Lesiones Personales",
    "CMHP":  "Hurto Personas",
    "CMHR":  "Hurto Residencias",
    "CMHA":  "Hurto Autos",
    "CMHB":  "Hurto Bicicletas",
    "CMHC":  "Hurto Comercio",
    "CMHCE": "Hurto Celulares",
    "CMHM":  "Hurto Motos",
    "CMDS":  "Delitos Sexuales",
    "CMVI":  "Violencia Intrafamiliar",
}


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class TransformResult:
    step: str         # "f1_delitos", "f7_estrato", "silver_table", etc.
    status: str       # "updated" | "skipped" | "error"
    rows_out: int     # filas en el archivo de salida
    file_path: str    # ruta del archivo producido
    message: str      # descripcion del resultado

    def __str__(self) -> str:
        icon = {"updated": "[OK]", "skipped": "[--]", "error": "[!!]"}.get(self.status, "[?]")
        return (
            f"{icon} {self.step:<25} {self.status:<8} "
            f"rows={self.rows_out:>8,}  {self.message}"
        )


# ─── Estado persistente ───────────────────────────────────────────────────────

class TransformState:
    """Lee y escribe datos/procesados/.transform_state.json."""

    def __init__(self) -> None:
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        if STATE_FILE.exists():
            try:
                self._data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def save(self) -> None:
        STATE_FILE.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def get(self, step: str) -> dict:
        return self._data.get(step, {})

    def update(self, step: str, **kwargs) -> None:
        if step not in self._data:
            self._data[step] = {}
        self._data[step].update({
            "last_run": datetime.now().isoformat()[:19],
            **kwargs,
        })
        self.save()

    def all_steps(self) -> dict:
        return self._data


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _find_col(df_columns: list[str], candidates: list[str]) -> str | None:
    """Busca el primer nombre de columna que coincida (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df_columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def _source_changed(in_path: Path, saved: dict) -> bool:
    """True si el archivo Bronze cambio desde el ultimo transform."""
    if not in_path.exists():
        return False
    current_mtime = str(in_path.stat().st_mtime)
    return current_mtime != saved.get("src_mtime")


def _hora_a_franja(hora_int: int) -> str:
    for nombre, (inicio, fin) in FRANJAS.items():
        if inicio <= hora_int <= fin:
            return nombre
    return "noche"


# ─── Paso 1 — F1 Delitos → delitos_localidad_anio.parquet ───────────────────
#
# NOTA: F1 (Delito de Alto Impacto) es un dataset AGREGADO a nivel localidad
# con totales anuales en formato ANCHO (una fila por localidad, columnas por anio+tipo).
# NO contiene registros individuales con lat/lon/UPZ.
# La variable Y para el modelo viene de F5 NUSE (ver transform_f5_nuse).
#
# Este paso produce una tabla de referencia para el EDA:
# delitos_localidad_anio.parquet (localidad x anio x tipo_delito → n_delitos)

def transform_f1_delitos(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Transforma el dataset de Delito de Alto Impacto (F1) de formato ancho
    a formato largo para el EDA a nivel localidad x anio x tipo.

    F1 es un dataset AGREGADO (21 localidades, totales anuales 2018-2026).
    NO tiene datos individuales con UPZ. La variable objetivo del modelo
    viene de F5 NUSE — ver transform_f5_nuse().

    Entrada:  datos/raw/f1_delito_alto_impacto.parquet
    Salida:   datos/procesados/delitos_localidad_anio.parquet

    Columnas producidas:
        cod_localidad, nom_localidad, anio, tipo_delito, n_delitos
    """
    import re
    import polars as pl

    step     = "f1"
    in_path  = RAW_DIR / "f1_delito_alto_impacto.parquet"
    out_path = PROC_DIR / "delitos_localidad_anio.parquet"
    saved    = state.get(step)

    if not in_path.exists():
        return TransformResult(step, "error", 0, str(out_path),
                               "Bronze no disponible — correr: python src/pipeline.py --source f1")

    if not force and out_path.exists() and not _source_changed(in_path, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "Bronze sin cambios desde ultimo transform")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] transformaria F1 (wide localidad) -> long localidad x anio x tipo")

    try:
        if verbose:
            print("    Leyendo parquet Bronze F1 (formato ancho: 21 localidades x 127 cols)...")
        df = pl.read_parquet(in_path)

        # Columnas identificadoras de la localidad
        loc_code_col = _find_col(df.columns, ["CMIULOCAL", "cmiulocal", "COD_LOCAL", "cod_local"])
        loc_name_col = _find_col(df.columns, ["CMNOMLOCAL", "cmnomlocal", "NOM_LOCAL", "nom_local"])

        if not loc_code_col:
            loc_code_col = df.columns[0]
        if not loc_name_col and len(df.columns) > 1:
            loc_name_col = df.columns[1]

        # Patron de columnas de crimen: CM<TIPO><YY>CONT o CM<TIPO><YY>CON
        # Prefijos ordenados de mas largo a mas corto para evitar match greedy incorrecto
        prefixes_sorted = sorted(F1_TIPO_MAP.keys(), key=len, reverse=True)
        crime_pat = re.compile(
            r"^(" + "|".join(re.escape(p) for p in prefixes_sorted) + r")(\d{2})(CONT|CON)$",
            re.IGNORECASE,
        )

        rows_long = []
        for row in df.iter_rows(named=True):
            cod = str(row.get(loc_code_col, "")).strip()
            nom = str(row.get(loc_name_col, "")).strip()
            for col, val in row.items():
                m = crime_pat.match(col)
                if not m:
                    continue
                prefix  = m.group(1).upper()
                year_yy = int(m.group(2))
                anio    = 2000 + year_yy
                tipo    = F1_TIPO_MAP.get(prefix, prefix)
                try:
                    n = int(float(val)) if val not in (None, "") else 0
                except (ValueError, TypeError):
                    n = 0
                rows_long.append({
                    "cod_localidad": cod,
                    "nom_localidad": nom,
                    "anio":          anio,
                    "tipo_delito":   tipo,
                    "n_delitos":     n,
                })

        if not rows_long:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontraron columnas de crimen con patron CM<TIPO><YY>CONT")

        result = (
            pl.DataFrame(rows_long)
            .with_columns([
                pl.col("cod_localidad").cast(pl.Utf8),
                pl.col("nom_localidad").cast(pl.Utf8),
                pl.col("anio").cast(pl.Int32),
                pl.col("tipo_delito").cast(pl.Utf8),
                pl.col("n_delitos").cast(pl.Int64),
            ])
            .sort(["cod_localidad", "anio", "tipo_delito"])
        )

        result.write_parquet(out_path)
        rows = len(result)
        anios = sorted(result["anio"].unique().to_list())
        if verbose:
            print(f"    {rows:,} filas | {result['cod_localidad'].n_unique()} localidades "
                  f"| anios {anios[0]}-{anios[-1]} | {result['tipo_delito'].n_unique()} tipos")
        state.update(step, src_mtime=str(in_path.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} filas | {result['cod_localidad'].n_unique()} localidades "
                               f"| anios {anios[0]}-{anios[-1]}")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 2 — F3 Clima → clima_diario.parquet ────────────────────────────────

def transform_f3_clima(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Agrega clima horario a nivel diario y mensual.

    Entrada:  datos/raw/f3_clima_bogota.parquet  (horario)
    Salida:   datos/procesados/clima_diario.parquet

    Columnas producidas:
        fecha (YYYY-MM-DD), temperatura_c (promedio dia),
        precipitacion_mm (acumulado dia), windspeed_promedio
    """
    import polars as pl

    step     = "f3"
    in_path  = RAW_DIR / "f3_clima_bogota.parquet"
    out_path = PROC_DIR / "clima_diario.parquet"
    saved    = state.get(step)

    if not in_path.exists():
        return TransformResult(step, "error", 0, str(out_path),
                               "Bronze no disponible — correr: python src/pipeline.py --source f3")

    if not force and out_path.exists() and not _source_changed(in_path, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "Bronze sin cambios desde ultimo transform")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] agregaria clima horario -> diario")

    try:
        df = pl.read_parquet(in_path)

        # Parsear columna time -> fecha
        df = df.with_columns(
            pl.col("time").str.slice(0, 10).alias("fecha")
        )

        # Agregar horario -> diario
        agg_exprs = []
        if "temperature_2m" in df.columns:
            agg_exprs.append(pl.col("temperature_2m").mean().round(2).alias("temperatura_c"))
        if "precipitation" in df.columns:
            agg_exprs.append(pl.col("precipitation").sum().round(2).alias("precipitacion_mm"))
        if "windspeed_10m" in df.columns:
            agg_exprs.append(pl.col("windspeed_10m").mean().round(2).alias("windspeed_promedio"))

        if not agg_exprs:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontraron columnas climaticas esperadas en F3")

        daily = df.group_by("fecha").agg(agg_exprs).sort("fecha")

        # Agregar columnas de fecha para joins
        daily = daily.with_columns([
            pl.col("fecha").str.slice(0, 4).cast(pl.Int32).alias("anio"),
            pl.col("fecha").str.slice(5, 2).cast(pl.Int32).alias("mes"),
            pl.col("fecha").str.slice(8, 2).cast(pl.Int32).alias("dia"),
        ])

        daily.write_parquet(out_path)
        rows = len(daily)
        state.update(step, src_mtime=str(in_path.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        if verbose:
            print(f"    {rows:,} dias | {daily['fecha'].min()} a {daily['fecha'].max()}")
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} dias | {daily['fecha'].min()} a {daily['fecha'].max()}")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 3 — F7 Estratificacion → estrato_por_upz.csv ───────────────────────

def transform_f7_estrato(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Spatial join manzanas (F7) contra UPZs (F2) para calcular el
    estrato promedio ponderado por UPZ.

    ADVERTENCIA: este paso carga ~115,000 poligonos en RAM.
    En Colab gratuito puede agotar memoria. Si falla, usar Colab Pro
    o ejecutar localmente y subir estrato_por_upz.csv al repo.

    Entrada:  datos/raw/f7_estratificacion.parquet
              datos/raw/f2_upz.geojson
    Salida:   datos/procesados/estrato_por_upz.csv

    Columnas producidas:
        upz_cod, estrato_promedio_upz, n_manzanas_upz
    """
    step     = "f7"
    in_f7    = RAW_DIR / "f7_estratificacion.parquet"
    in_f2    = RAW_DIR / "f2_upz.geojson"
    out_path = PROC_DIR / "estrato_por_upz.csv"
    saved    = state.get(step)

    for p, label in [(in_f7, "F7 estratificacion"), (in_f2, "F2 UPZ shapefile")]:
        if not p.exists():
            return TransformResult(step, "error", 0, str(out_path),
                                   f"Bronze no disponible: {label} — correr pipeline primero")

    if not force and out_path.exists() and not _source_changed(in_f7, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "F7 sin cambios — estrato_por_upz.csv reutilizado")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] spatial join ~115K manzanas x 112 UPZs (operacion pesada)")

    try:
        import geopandas as gpd
        import polars as pl
        from shapely import wkt

        if verbose:
            print("    Cargando manzanas de estratificacion (~115K poligonos)...")
        df_estrato = pl.read_parquet(in_f7)

        # Encontrar columna de estrato
        estrato_col = _find_col(df_estrato.columns,
                                ["estrato", "ESTRATO", "estrato_social", "ESTRATO_SOCIAL"])
        if not estrato_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna 'estrato' en F7")

        # Convertir a GeoDataFrame usando geometry_wkt
        if "geometry_wkt" not in df_estrato.columns:
            return TransformResult(step, "error", 0, str(out_path),
                                   "F7 no tiene columna geometry_wkt — re-descargar con pipeline --force f7")

        if verbose:
            print("    Reconstruyendo geometrias WKT -> shapely...")
        # F7 usa CRS PCS_CarMAGBOG = Sistema de Referencia Local de Bogota (Catastro)
        # Parametros verificados: lat_0=4.598°N, lon_0=74.081°W, FE=92334.879, FN=109319.672
        # Con estos parametros, coordenadas ~(98000,109000) mapean a Bogota correctamente.
        # NO usar EPSG:3116 — ese codigo usa otra configuracion y da resultados incorrectos.
        import pyproj
        bogota_local_crs = pyproj.CRS.from_dict({
            "proj": "tmerc",
            "lat_0": 4.598055556,
            "lon_0": -74.081361111,
            "k": 1.0,
            "x_0": 92334.879,
            "y_0": 109319.672,
            "ellps": "GRS80",
            "units": "m",
        })
        gdf_manzanas = gpd.GeoDataFrame(
            df_estrato.to_pandas(),
            geometry=df_estrato["geometry_wkt"].to_pandas().apply(wkt.loads),
            crs=bogota_local_crs,
        )
        # Calcular centroide en coordenadas proyectadas (mas preciso antes de reproyectar)
        gdf_manzanas["geometry"] = gdf_manzanas.geometry.centroid
        # Reproyectar a EPSG:4326 para que coincida con F2 UPZ shapefile
        gdf_manzanas = gdf_manzanas.to_crs("EPSG:4326")
        gdf_manzanas[estrato_col] = (
            gdf_manzanas[estrato_col]
            .astype(str).str.strip()
            .replace({"": None})
            .astype(float, errors="ignore")
        )
        gdf_manzanas = gdf_manzanas.dropna(subset=[estrato_col])

        if verbose:
            print("    Cargando UPZ shapefile...")
        gdf_upz = gpd.read_file(in_f2)

        # Detectar columna codigo UPZ en el shapefile (F2 usa "CODIGO_UPZ")
        upz_id_col = _find_col(list(gdf_upz.columns), UPZ_COL_CANDIDATES)
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   f"No se encontro columna UPZ en F2. Cols: {list(gdf_upz.columns)}")

        if verbose:
            print("    Ejecutando spatial join centroide manzana -> UPZ...")
        joined = gpd.sjoin(
            gdf_manzanas[[estrato_col, "geometry"]],
            gdf_upz[[upz_id_col, "geometry"]].rename(columns={upz_id_col: "upz_cod"}),
            how="inner",
            predicate="within",
        )

        # Calcular promedio ponderado (todas las manzanas tienen mismo peso)
        result = (
            joined.groupby("upz_cod")[estrato_col]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"mean": "estrato_promedio_upz", "count": "n_manzanas_upz"})
        )
        result["estrato_promedio_upz"] = result["estrato_promedio_upz"].round(2)
        result["upz_cod"] = result["upz_cod"].astype(str).str.strip()

        result.to_csv(out_path, index=False, encoding="utf-8")
        rows = len(result)

        if verbose:
            print(f"    {rows} UPZs con estrato promedio calculado")
            print(f"    Rango estrato: {result['estrato_promedio_upz'].min():.2f} - "
                  f"{result['estrato_promedio_upz'].max():.2f}")

        state.update(step, src_mtime=str(in_f7.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows} UPZs | estrato {result['estrato_promedio_upz'].min():.1f}"
                               f"-{result['estrato_promedio_upz'].max():.1f}")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 4 — F4 Cuadrantes + F2 UPZ → features_cuadrantes_upz.csv ──────────

def transform_f4_cuadrantes(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Spatial join cuadrantes policiales x UPZ para calcular densidad de cobertura.

    Entrada:  datos/raw/f4_cuadrantes.geojson
              datos/raw/f2_upz.geojson
    Salida:   datos/procesados/features_cuadrantes_upz.csv

    Columnas producidas:
        upz_cod, n_cuadrantes, area_upz_km2, cuadrantes_por_km2
    """
    step     = "f4"
    in_f4    = RAW_DIR / "f4_cuadrantes.geojson"
    in_f2    = RAW_DIR / "f2_upz.geojson"
    out_path = PROC_DIR / "features_cuadrantes_upz.csv"
    saved    = state.get(step)

    for p, label in [(in_f4, "F4 cuadrantes"), (in_f2, "F2 UPZ")]:
        if not p.exists():
            return TransformResult(step, "error", 0, str(out_path),
                                   f"Bronze no disponible: {label}")

    if not force and out_path.exists() and not _source_changed(in_f4, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "Cuadrantes sin cambios")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] spatial join cuadrantes x UPZ")

    try:
        import geopandas as gpd

        if verbose:
            print("    Cargando cuadrantes y UPZs...")
        gdf_cuad = gpd.read_file(in_f4)
        gdf_upz  = gpd.read_file(in_f2)

        # Asegurar mismo CRS
        if gdf_cuad.crs != gdf_upz.crs:
            gdf_cuad = gdf_cuad.to_crs(gdf_upz.crs)

        upz_id_col = _find_col(list(gdf_upz.columns), UPZ_COL_CANDIDATES)
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   f"No se encontro columna UPZ en F2. Columnas disponibles: {list(gdf_upz.columns)}")

        # Usar centroide del cuadrante para el join
        gdf_cuad_pts = gdf_cuad.copy()
        gdf_cuad_pts["geometry"] = gdf_cuad_pts.geometry.centroid

        if verbose:
            print("    Ejecutando spatial join cuadrantes -> UPZ...")
        joined = gpd.sjoin(
            gdf_cuad_pts[["geometry"]],
            gdf_upz[[upz_id_col, "geometry"]].rename(columns={upz_id_col: "upz_cod"}),
            how="left",
            predicate="within",
        )

        # Contar cuadrantes por UPZ
        n_cuad = joined.groupby("upz_cod").size().reset_index(name="n_cuadrantes")

        # Calcular area de cada UPZ en km2
        gdf_upz_proj = gdf_upz.to_crs("EPSG:3116")   # proyeccion Colombia
        gdf_upz_proj["area_upz_km2"] = (gdf_upz_proj.geometry.area / 1e6).round(3)
        areas = gdf_upz_proj[[upz_id_col, "area_upz_km2"]].rename(
            columns={upz_id_col: "upz_cod"}
        )
        areas["upz_cod"] = areas["upz_cod"].astype(str).str.strip()

        result = n_cuad.merge(areas, on="upz_cod", how="left")
        result["cuadrantes_por_km2"] = (
            result["n_cuadrantes"] / result["area_upz_km2"].replace(0, float("nan"))
        ).round(4)

        result.to_csv(out_path, index=False, encoding="utf-8")
        rows = len(result)
        if verbose:
            print(f"    {rows} UPZs | cuadrantes promedio: {result['n_cuadrantes'].mean():.1f}")
        state.update(step, src_mtime=str(in_f4.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows} UPZs | {result['n_cuadrantes'].sum()} cuadrantes totales")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 5 — F8 TransMilenio + F2 UPZ → features_tm_upz.csv ────────────────

def transform_f8_transmilenio(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Calcula n_estaciones_tm y dist_tm_metros por UPZ.

    Entrada:  datos/raw/f8_transmilenio.geojson
              datos/raw/f2_upz.geojson
    Salida:   datos/procesados/features_tm_upz.csv

    Columnas producidas:
        upz_cod, n_estaciones_tm, dist_tm_metros
    """
    step     = "f8"
    in_f8    = RAW_DIR / "f8_transmilenio.geojson"
    in_f2    = RAW_DIR / "f2_upz.geojson"
    out_path = PROC_DIR / "features_tm_upz.csv"
    saved    = state.get(step)

    for p, label in [(in_f8, "F8 TransMilenio"), (in_f2, "F2 UPZ")]:
        if not p.exists():
            return TransformResult(step, "error", 0, str(out_path),
                                   f"Bronze no disponible: {label}")

    if not force and out_path.exists() and not _source_changed(in_f8, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "TransMilenio sin cambios")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] spatial join estaciones TM x UPZ")

    try:
        import geopandas as gpd
        import numpy as np

        if verbose:
            print("    Cargando estaciones TM y UPZs...")
        gdf_tm  = gpd.read_file(in_f8)
        gdf_upz = gpd.read_file(in_f2)

        if gdf_tm.crs != gdf_upz.crs:
            gdf_tm = gdf_tm.to_crs(gdf_upz.crs)

        upz_id_col = _find_col(list(gdf_upz.columns), UPZ_COL_CANDIDATES)
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   f"No se encontro columna UPZ en F2. Cols: {list(gdf_upz.columns)}")

        # n_estaciones_tm por UPZ
        joined = gpd.sjoin(
            gdf_tm[["geometry"]],
            gdf_upz[[upz_id_col, "geometry"]].rename(columns={upz_id_col: "upz_cod"}),
            how="left",
            predicate="within",
        )
        n_estaciones = joined.groupby("upz_cod").size().reset_index(name="n_estaciones_tm")

        # dist_tm_metros = distancia del centroide de la UPZ a la estacion mas cercana
        # Proyectar a metros para calcular distancias reales
        gdf_upz_proj = gdf_upz[[upz_id_col, "geometry"]].to_crs("EPSG:3116")
        gdf_tm_proj  = gdf_tm[["geometry"]].to_crs("EPSG:3116")

        centroides_upz = gdf_upz_proj.copy()
        centroides_upz["geometry"] = centroides_upz.geometry.centroid

        if verbose:
            print("    Calculando distancia al TM mas cercano por UPZ...")
        distancias = []
        for _, row in centroides_upz.iterrows():
            dist_min = gdf_tm_proj.geometry.distance(row.geometry).min()
            distancias.append({
                "upz_cod": str(row[upz_id_col]).strip(),
                "dist_tm_metros": round(float(dist_min), 1),
            })

        import pandas as pd
        df_dist = pd.DataFrame(distancias)

        # Combinar conteo + distancia
        n_estaciones["upz_cod"] = n_estaciones["upz_cod"].astype(str).str.strip()
        result = df_dist.merge(n_estaciones, on="upz_cod", how="left")
        result["n_estaciones_tm"] = result["n_estaciones_tm"].fillna(0).astype(int)

        result.to_csv(out_path, index=False, encoding="utf-8")
        rows = len(result)
        if verbose:
            print(f"    {rows} UPZs | dist media TM: {result['dist_tm_metros'].mean():.0f}m")
        state.update(step, src_mtime=str(in_f8.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows} UPZs | dist media al TM: "
                               f"{result['dist_tm_metros'].mean():.0f}m")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 6 — F5 NUSE → nuse_upz_mes.parquet + delitos_upz_mes.parquet ───────
#
# F5 (NUSE 123) contiene TODOS los incidentes reportados al 123 (2025-2026).
# Este paso produce DOS archivos:
#   1. nuse_upz_mes.parquet    — totales por UPZ x mes (todos los tipos, para proporciones)
#   2. delitos_upz_mes.parquet — TODOS los 86 tipos × UPZ × mes + flag es_crimen
#                                 ~111K filas — sin filtrar, sin perder informacion
#
# La columna es_crimen=True marca los 19 tipos de alto impacto criminal.
# Los demas tipos (ruido, trafico, emergencias medicas, etc.) son indicadores
# de desorden social que el modelo Gold puede usar como features correlacionados.

def transform_f5_nuse(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Agrega incidentes NUSE 123. Produce dos archivos:
      - nuse_upz_mes.parquet    : totales por UPZ x mes (todos los tipos)
      - delitos_upz_mes.parquet : TODOS los 86 tipos por UPZ x mes x tipo_crimen
                                  con flag es_crimen y lags — BASE de la tabla Silver.
                                  ~111K filas (sin filtrar tipos).

    NO se filtra a tipos criminales: todos los 86 tipos del NUSE se mantienen.
    La columna es_crimen=True marca los 19 tipos de alto impacto criminal.
    Los demas tipos (RUIDO, ACCIDENTE TRANSITO, MALTRATO, etc.) son indicadores
    de desorden urbano que el modelo puede aprovechar como features correlacionados
    con la criminalidad.

    Entrada:  datos/raw/f5_nuse_123.parquet
    Salidas:  datos/procesados/nuse_upz_mes.parquet
              datos/procesados/delitos_upz_mes.parquet

    Columnas de delitos_upz_mes:
        upz_cod, anio, mes, tipo_crimen, es_crimen, n_delitos,
        n_delitos_upz_4sem (lag por tipo), n_delitos_upz_8sem (lag acum por tipo)
    """
    import polars as pl

    step        = "f5"
    in_path     = RAW_DIR / "f5_nuse_123.parquet"
    out_nuse    = PROC_DIR / "nuse_upz_mes.parquet"
    out_delitos = PROC_DIR / "delitos_upz_mes.parquet"
    saved       = state.get(step)

    if not in_path.exists():
        return TransformResult(step, "error", 0, str(out_nuse),
                               "Bronze no disponible — correr: python src/pipeline.py --source f5")

    if not force and out_nuse.exists() and out_delitos.exists() and not _source_changed(in_path, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_nuse),
                               "NUSE sin cambios")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_nuse),
                               "[DRY-RUN] agregaria NUSE por UPZ x mes x tipo_crimen (2 archivos)")

    try:
        df = pl.read_parquet(in_path)

        # Encontrar columnas clave
        upz_col   = _find_col(df.columns, ["COD_UPZ", "cod_upz", "UPZ", "upz"])
        anio_col  = _find_col(df.columns, ["ANIO", "anio", "AÑO", "año", "year"])
        mes_col   = _find_col(df.columns, ["MES", "mes", "month"])
        cant_col  = _find_col(df.columns, ["CANT_INCIDENTES", "cant_incidentes",
                                           "cantidad", "CANTIDAD", "count"])
        tipo_col  = _find_col(df.columns, ["TIPO_DETALLE", "tipo_detalle",
                                           "TIPO_INCIDENTE", "tipo_incidente"])

        missing = [name for name, col in
                   [("UPZ", upz_col), ("ANIO", anio_col), ("MES", mes_col)]
                   if col is None]
        if missing:
            return TransformResult(step, "error", 0, str(out_nuse),
                                   f"Columnas no encontradas en F5: {missing}")

        # Normalizar codigo UPZ: "UPZ67" → "67", "UPR3" → ignorar (rurales)
        df = df.with_columns(
            pl.col(upz_col).cast(pl.Utf8)
            .str.replace_all(r"[Uu][Pp][Zz]", "")
            .str.replace_all(r"[Uu][Pp][Rr]", "RURAL_")
            .str.strip_chars()
            .alias("upz_cod")
        ).filter(
            ~pl.col("upz_cod").str.starts_with("RURAL_")
        )

        # Columna de cantidad
        if cant_col:
            df = df.with_columns(
                pl.col(cant_col).cast(pl.Int64, strict=False).alias("_cant")
            )
        else:
            df = df.with_columns(pl.lit(1).cast(pl.Int64).alias("_cant"))

        # Normalizar anio y mes a entero
        df = df.with_columns([
            pl.col(anio_col).cast(pl.Int32, strict=False).alias("anio"),
            pl.col(mes_col).cast(pl.Int32, strict=False).alias("mes"),
        ])

        # ── ARCHIVO 1: todos los tipos de NUSE (UPZ x mes) ──────────────────
        nuse_all = (
            df.group_by(["upz_cod", "anio", "mes"])
            .agg(pl.col("_cant").sum().alias("n_incidentes_nuse"))
            .sort(["upz_cod", "anio", "mes"])
        )
        nuse_all.write_parquet(out_nuse)
        if verbose:
            print(f"    nuse_upz_mes: {len(nuse_all):,} filas | "
                  f"{nuse_all['n_incidentes_nuse'].sum():,} incidentes totales")

        # ── ARCHIVO 2: TODOS los tipos × UPZ × mes × tipo_crimen ───────────
        # Sin filtro: se conservan los 86 tipos del NUSE.
        # es_crimen=True marca los 19 tipos de alto impacto criminal.
        # Los demas tipos son indicadores de desorden urbano usables como features.
        if tipo_col:
            monthly = (
                df.group_by(["upz_cod", "anio", "mes", tipo_col])
                .agg(pl.col("_cant").sum().alias("n_delitos"))
                .rename({tipo_col: "tipo_crimen"})
                .with_columns(
                    pl.col("tipo_crimen").is_in(list(CRIME_TYPES_NUSE)).alias("es_crimen")
                )
                .sort(["upz_cod", "anio", "mes", "tipo_crimen"])
            )
            if verbose:
                n_crimen = int(monthly.filter(pl.col("es_crimen"))["n_delitos"].sum())
                n_total  = int(monthly["n_delitos"].sum())
                n_tipos_c = monthly.filter(pl.col("es_crimen"))["tipo_crimen"].n_unique()
                print(f"    Todos los tipos: {monthly['tipo_crimen'].n_unique()} | "
                      f"incidentes criminales: {n_crimen:,} de {n_total:,} "
                      f"({n_tipos_c} tipos con es_crimen=True)")
        else:
            # Sin columna de tipo, usar todos los incidentes como proxy
            monthly = (
                df.group_by(["upz_cod", "anio", "mes"])
                .agg(pl.col("_cant").sum().alias("n_delitos"))
                .with_columns([
                    pl.lit("TODOS").alias("tipo_crimen"),
                    pl.lit(True).alias("es_crimen"),
                ])
                .sort(["upz_cod", "anio", "mes"])
            )

        # Lag features por UPZ x tipo_crimen
        # Ej: lag de HURTO en UPZ-67 mes-3 = HURTO en UPZ-67 mes-2
        monthly = monthly.sort(["upz_cod", "tipo_crimen", "anio", "mes"]).with_columns([
            pl.col("n_delitos")
            .shift(1)
            .over(["upz_cod", "tipo_crimen"])
            .alias("n_delitos_upz_4sem"),
            (
                pl.col("n_delitos").shift(1).over(["upz_cod", "tipo_crimen"]) +
                pl.col("n_delitos").shift(2).over(["upz_cod", "tipo_crimen"]).fill_null(0)
            ).alias("n_delitos_upz_8sem"),
        ]).sort(["upz_cod", "anio", "mes", "tipo_crimen"])

        # Reordenar columnas: dimensiones primero, luego metricas
        col_order = (
            ["upz_cod", "anio", "mes", "tipo_crimen", "es_crimen",
             "n_delitos", "n_delitos_upz_4sem", "n_delitos_upz_8sem"]
        )
        monthly = monthly.select([c for c in col_order if c in monthly.columns])

        monthly.write_parquet(out_delitos)
        rows = len(monthly)
        n_tipos = monthly["tipo_crimen"].n_unique() if "tipo_crimen" in monthly.columns else 0

        if verbose:
            print(f"    delitos_upz_mes: {rows:,} filas | {monthly['upz_cod'].n_unique()} UPZs | "
                  f"{n_tipos} tipos crimen | n_delitos total {monthly['n_delitos'].sum():,}")

        state.update(step,
                     src_mtime=str(in_path.stat().st_mtime),
                     rows_out=rows,
                     rows_nuse=len(nuse_all),
                     file_path=str(out_nuse))
        return TransformResult(step, "updated", rows, str(out_nuse),
                               f"nuse={len(nuse_all):,} filas | "
                               f"delitos={rows:,} filas ({n_tipos} tipos) | "
                               f"{monthly['upz_cod'].n_unique()} UPZs")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_nuse), str(exc))


# ─── Paso 7 — Tabla Silver final → silver_upz_mes.parquet ───────────────────

def build_silver_table(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Une todos los pasos anteriores en una sola tabla Silver.
    Calcula ademas ratio_nuse_delitos_upz.

    Este paso DEPENDE de que los anteriores ya hayan corrido.

    ESTRUCTURA ACTUALIZADA: silver_upz_mes ahora tiene granularidad
    UPZ x mes x tipo_crimen (~15-25K filas) para cumplir el requisito
    de 10K filas del concurso y enriquecer el modelo XGBoost.

    Las features estaticas (estrato, cuadrantes, TM) se repiten para
    cada tipo de crimen en el mismo UPZ x mes — son caracteristicas
    del espacio, no del tipo de delito.

    ratio_nuse_delitos_upz = NUSE_total / delitos_totales por UPZ x mes
    (mismo valor para todos los tipos en el mismo UPZ x mes).

    Entrada:  datos/procesados/delitos_upz_mes.parquet  <- de F5 (UPZ x mes x tipo)
              datos/procesados/clima_diario.parquet
              datos/procesados/nuse_upz_mes.parquet     <- de F5 (todos los tipos)
              datos/procesados/estrato_por_upz.csv
              datos/procesados/features_cuadrantes_upz.csv
              datos/procesados/features_tm_upz.csv
    Salida:   datos/procesados/silver_upz_mes.parquet

    Esta tabla tiene TODAS las variables candidatas.
    La capa Gold (Notebook 03) decide cuales entran al modelo.
    """
    import polars as pl

    step     = "silver"
    out_path = PROC_DIR / "silver_upz_mes.parquet"

    required = {
        "delitos":    PROC_DIR / "delitos_upz_mes.parquet",
        "clima":      PROC_DIR / "clima_diario.parquet",
        "nuse":       PROC_DIR / "nuse_upz_mes.parquet",
        "estrato":    PROC_DIR / "estrato_por_upz.csv",
        "cuadrantes": PROC_DIR / "features_cuadrantes_upz.csv",
        "tm":         PROC_DIR / "features_tm_upz.csv",
    }

    missing = [k for k, p in required.items() if not p.exists()]
    if missing:
        return TransformResult(step, "error", 0, str(out_path),
                               f"Pasos previos no completados: {missing}. "
                               f"Correr run_transform() completo primero.")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] construiria tabla Silver final (join de 6 fuentes)")

    try:
        if verbose:
            print("    Cargando tablas intermedias...")

        base     = pl.read_parquet(required["delitos"])
        clima    = pl.read_parquet(required["clima"])
        nuse     = pl.read_parquet(required["nuse"])
        estrato  = pl.read_csv(required["estrato"])
        cuad     = pl.read_csv(required["cuadrantes"])   # key corregido: "cuadrantes"
        tm       = pl.read_csv(required["tm"])

        # Estandarizar tipos de upz_cod en todas las tablas
        for df_name, df in [("estrato", estrato), ("cuad", cuad), ("tm", tm)]:
            pass  # ya son pl.DataFrame de read_csv, upz_cod es Utf8

        # Asegurar upz_cod como string en base
        base = base.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())

        # JOIN 0: localidad desde F5 raw (UPZ → localidad) — src/geo_utils.py,
        # compartido con scripts/seed_supabase.py::seed_geometrias(). Resuelve
        # UPZs con mas de una localidad en F5 por moda (localidad mas frecuente),
        # no por la primera fila que aparezca.
        if (RAW_DIR / "f5_nuse_123.parquet").exists():
            upz_loc = build_upz_localidad_crosswalk(RAW_DIR / "f5_nuse_123.parquet")
            base = base.join(upz_loc, on="upz_cod", how="left")
            if verbose:
                n_loc = base["cod_localidad"].drop_nulls().n_unique() if "cod_localidad" in base.columns else 0
                print(f"    Localidades asignadas: {n_loc} localidades en {base['upz_cod'].n_unique()} UPZs")

        # JOIN 1: agregar clima mensual promedio (temperatura y lluvia del mes)
        clima_mensual = clima.group_by(["anio", "mes"]).agg([
            pl.col("temperatura_c").mean().round(2).alias("temperatura_c"),
            pl.col("precipitacion_mm").sum().round(2).alias("precipitacion_mm_mes"),
        ])
        silver = base.join(clima_mensual, on=["anio", "mes"], how="left")

        # JOIN 2: NUSE total UPZ x mes → calcular proporcion del tipo vs total
        # ratio_tipo_nuse = n_delitos_tipo / n_incidentes_nuse_total_upz_mes
        # Ej: HURTO EFECTUADO en UPZ-67 en ene-2025 representa X% del total de llamadas
        nuse = nuse.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
        silver = silver.join(nuse, on=["upz_cod", "anio", "mes"], how="left")
        silver = silver.with_columns(
            pl.when(pl.col("n_incidentes_nuse") > 0)
            .then(pl.col("n_delitos") / pl.col("n_incidentes_nuse"))
            .otherwise(pl.lit(0.0))
            .round(4)
            .alias("ratio_tipo_nuse_total")
        )

        # JOIN 3: estrato promedio por UPZ (estatico — no depende de mes)
        estrato = estrato.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
        silver = silver.join(estrato[["upz_cod", "estrato_promedio_upz"]],
                             on="upz_cod", how="left")

        # JOIN 4: cuadrantes por UPZ
        cuad = cuad.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
        silver = silver.join(cuad[["upz_cod", "cuadrantes_por_km2", "area_upz_km2"]],
                             on="upz_cod", how="left")

        # JOIN 5: TransMilenio por UPZ
        tm = tm.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
        silver = silver.join(tm[["upz_cod", "n_estaciones_tm", "dist_tm_metros"]],
                             on="upz_cod", how="left")

        # Columnas temporales adicionales
        silver = silver.with_columns([
            ((pl.col("mes") >= 6) & (pl.col("mes") <= 8)).alias("es_mitad_anio"),
        ])

        # Ordenar por UPZ x mes x tipo_crimen
        sort_cols = ["upz_cod", "anio", "mes"]
        if "tipo_crimen" in silver.columns:
            sort_cols.append("tipo_crimen")
        silver = silver.sort(sort_cols)
        silver.write_parquet(out_path)
        rows = len(silver)

        n_tipos = silver["tipo_crimen"].n_unique() if "tipo_crimen" in silver.columns else 1
        n_upzs  = silver["upz_cod"].n_unique()

        if verbose:
            print(f"    {rows:,} filas | {n_upzs} UPZs | {n_tipos} tipos crimen | "
                  f"{len(silver.columns)} columnas")
            nulls = {c: silver[c].null_count() for c in silver.columns if silver[c].null_count() > 0}
            if nulls:
                print(f"    Nulls por columna: {nulls}")

        state.update(step, rows_out=rows, columns=silver.columns, file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} filas | {len(silver.columns)} cols | "
                               f"{n_upzs} UPZs | {n_tipos} tipos crimen")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


def transform_f9_boletines() -> int:
    """
    F9 — Extrae texto de los PDFs de boletines SCJ y genera corpus JSON para Claude API.

    Salida:
      datos/procesados/boletines_corpus.json  — lista de {filename, texto, n_paginas, n_chars}
      datos/procesados/boletines_stats.parquet — estadisticas parseadas (si hay tablas)

    El corpus JSON es el insumo para los prompts de Claude API en Modulos 3 y 4.
    """
    import json

    try:
        import pdfplumber
    except ImportError:
        print("  [F9] pdfplumber no instalado. Ejecuta: pip install pdfplumber")
        return 0

    boletines_dir = RAW_DIR / "boletines_scj"
    if not boletines_dir.exists():
        print(f"  [F9] Directorio {boletines_dir} no existe. Ejecuta primero extract_f9_scj_boletines()")
        return 0

    pdfs = sorted(boletines_dir.glob("*.pdf"))
    if not pdfs:
        print(f"  [F9] No hay PDFs en {boletines_dir}")
        return 0

    corpus = []
    for pdf_path in pdfs:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
                n_pags = len(pdf.pages)
            corpus.append({
                "filename": pdf_path.name,
                "texto": texto.strip(),
                "n_paginas": n_pags,
                "n_chars": len(texto),
            })
            print(f"    {pdf_path.name}: {n_pags} pags, {len(texto):,} chars")
        except Exception as e:
            print(f"    Error procesando {pdf_path.name}: {e}")

    out_path = PROC_DIR / "boletines_corpus.json"
    out_path.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total_chars = sum(d["n_chars"] for d in corpus)
    print(f"  [F9] Corpus: {len(corpus)} boletines | {total_chars:,} chars totales → {out_path.name}")
    return len(corpus)


# ─── Mapa de pasos ────────────────────────────────────────────────────────────

STEPS = {
    "f1": transform_f1_delitos,
    "f3": transform_f3_clima,
    "f4": transform_f4_cuadrantes,
    "f5": transform_f5_nuse,
    "f7": transform_f7_estrato,
    "f8": transform_f8_transmilenio,
    "silver": build_silver_table,
}

STEP_LABELS = {
    "f1":    "F1 DAI -> localidad x anio (EDA ref)",
    "f3":    "F3 Clima -> diario",
    "f4":    "F4 Cuadrantes -> features UPZ",
    "f5":    "F5 NUSE -> UPZ x mes x tipo_crimen",
    "f7":    "F7 Estrato -> promedio UPZ  [pesado]",
    "f8":    "F8 TransMilenio -> features UPZ",
    "silver":"Tabla Silver final (join de todo)",
}

# Orden de ejecucion: silver debe ir al final
STEP_ORDER = ["f1", "f3", "f4", "f5", "f7", "f8", "silver"]


# ─── Orquestador ──────────────────────────────────────────────────────────────

def run_transform(
    steps: Optional[list[str]] = None,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[TransformResult]:
    """
    Ejecuta la transformacion Silver para los pasos indicados.

    steps:   ["f1", "f3", "silver"] o None para todos en orden.
    force:   True -> recalcula aunque no haya cambios en el Bronze.
    dry_run: True -> informa que haria sin ejecutar.
    verbose: True -> imprime progreso detallado.

    Ejemplo:
        from src.transform import run_transform
        resultados = run_transform(verbose=True)
        for r in resultados:
            print(r)
    """
    state   = TransformState()
    to_run  = steps if steps else STEP_ORDER
    to_run  = [s[:2] if s.startswith("silver") else s[:2] for s in to_run]
    # normalizar: "f1_delitos" -> "f1", "silver_table" -> "si" -> buscar "silver"
    to_run  = [s if s in STEPS else next((k for k in STEPS if k.startswith(s)), s)
               for s in to_run]
    to_run  = [s for s in to_run if s in STEPS]

    # Respetar orden de dependencias
    to_run = sorted(to_run, key=lambda s: STEP_ORDER.index(s) if s in STEP_ORDER else 99)

    results: list[TransformResult] = []
    for key in to_run:
        fn = STEPS[key]
        if verbose:
            print(f"\n[{key.upper()}] {STEP_LABELS.get(key, key)}")
        result = fn(state, force=force, dry_run=dry_run, verbose=verbose)
        results.append(result)
        if not verbose:
            print(result)

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _print_status(state: TransformState) -> None:
    data = state.all_steps()
    print()
    print(f"{'Paso':<30} {'Estado':<8} {'Filas':>10}  {'Ultima ejecucion':<20}  Archivo")
    print("-" * 95)
    for key in STEP_ORDER:
        info    = data.get(key, {})
        status  = info.get("status", "pendiente") if info else "pendiente"
        rows    = f"{info.get('rows_out', 0):,}" if info.get("rows_out") else "-"
        last_r  = (info.get("last_run") or "-")[:19]
        fpath   = Path(info.get("file_path", "-")).name if info.get("file_path") else "-"
        label   = STEP_LABELS.get(key, key)
        # inferir status de si el archivo existe
        fp = info.get("file_path")
        if fp and Path(fp).exists() and not info.get("status"):
            status = "ok"
        print(f"{label:<30} {status:<8} {rows:>10}  {last_r:<20}  {fpath}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="transform",
        description="SeguroData - Capa Silver: limpieza, joins espaciales y agregacion por UPZ",
    )
    parser.add_argument("--step", "-s", nargs="+",
                        choices=list(STEPS.keys()), metavar="STEP",
                        help="pasos a ejecutar (f1 f3 f4 f5 f7 f8 silver). Sin flag -> todos")
    parser.add_argument("--force", "-f", action="store_true",
                        help="recalcular aunque Bronze no haya cambiado")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="muestra que ejecutaria sin hacerlo")
    parser.add_argument("--status", action="store_true",
                        help="muestra estado de todos los pasos y sale")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="output detallado con progreso")
    args = parser.parse_args()

    if args.status:
        _print_status(TransformState())
        return

    sep = "-" * 60
    print(f"\n{sep}")
    print("  SeguroData Bogota - Pipeline de transformacion (Silver)")
    print(sep)
    if args.dry_run:
        print("  [DRY-RUN] - no se escribira nada\n")

    results = run_transform(
        steps=args.step,
        force=args.force,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    print(f"\n{sep}")
    updated = sum(1 for r in results if r.status == "updated")
    skipped = sum(1 for r in results if r.status == "skipped")
    errors  = sum(1 for r in results if r.status == "error")
    print(f"  Resumen: {updated} actualizados  {skipped} sin cambios  {errors} errores")
    print(f"{sep}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
