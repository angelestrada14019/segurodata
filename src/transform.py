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

# ─── Columnas esperadas en Bronze ─────────────────────────────────────────────
# Nombres posibles para cada campo (el raw puede variar entre versiones del dataset)
UPZ_COL_CANDIDATES  = ["upz", "UPZ", "cod_upz", "COD_UPZ", "codigo_upz", "CODIGO_UPZ"]
TIPO_COL_CANDIDATES = ["tipologia_delito", "TIPOLOGIA_DELITO", "tipo_delito", "TIPO_DELITO"]
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


# ─── Paso 1 — F1 Delitos → delitos_upz_mes.parquet ───────────────────────────

def transform_f1_delitos(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Transforma el GeoJSON de Delito de Alto Impacto en una tabla
    agregada por UPZ x mes con lag features.

    Entrada:  datos/raw/f1_delito_alto_impacto.parquet
    Salida:   datos/procesados/delitos_upz_mes.parquet

    Columnas producidas:
        upz_cod, anio, mes, n_delitos, tipo_delito_dominante,
        n_delitos_upz_4sem (lag ~1 mes), n_delitos_upz_8sem (lag acum ~2 meses)
    """
    import polars as pl

    step     = "f1_delitos"
    in_path  = RAW_DIR / "f1_delito_alto_impacto.parquet"
    out_path = PROC_DIR / "delitos_upz_mes.parquet"
    saved    = state.get(step)

    if not in_path.exists():
        return TransformResult(step, "error", 0, str(out_path),
                               "Bronze no disponible — correr: python src/pipeline.py --source f1")

    if not force and out_path.exists() and not _source_changed(in_path, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "Bronze sin cambios desde ultimo transform")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] transformaria F1 delitos -> UPZ x mes")

    try:
        if verbose:
            print("    Leyendo parquet Bronze F1...")
        df = pl.read_parquet(in_path)
        n_raw = len(df)
        if verbose:
            print(f"    {n_raw:,} registros crudos")

        # 1. Filtrar coordenadas fuera de Bogota (si existen las columnas)
        lat_col = _find_col(df.columns, LAT_COL_CANDIDATES)
        lon_col = _find_col(df.columns, LON_COL_CANDIDATES)
        if lat_col and lon_col:
            df = df.with_columns([
                pl.col(lat_col).cast(pl.Float64, strict=False),
                pl.col(lon_col).cast(pl.Float64, strict=False),
            ]).filter(
                pl.col(lat_col).is_between(BOG_LAT_MIN, BOG_LAT_MAX) &
                pl.col(lon_col).is_between(BOG_LON_MIN, BOG_LON_MAX)
            )
            if verbose:
                print(f"    {len(df):,} registros dentro de Bogota ({n_raw - len(df):,} filtrados)")

        # 2. Parsear fecha -> anio, mes
        fecha_col = _find_col(df.columns, FECHA_COL_CANDIDATES)
        if not fecha_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna de fecha en F1")

        # Intentar varios formatos de fecha comunes en los datos de Bogota
        date_formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"]
        parsed = False
        for fmt in date_formats:
            try:
                df = df.with_columns(
                    pl.col(fecha_col).str.strptime(pl.Datetime, fmt, strict=False).alias("_fecha_dt")
                )
                if df["_fecha_dt"].drop_nulls().len() > 0:
                    parsed = True
                    break
            except Exception:
                continue

        if not parsed:
            return TransformResult(step, "error", 0, str(out_path),
                                   f"No se pudo parsear fecha desde columna '{fecha_col}'")

        df = df.with_columns([
            pl.col("_fecha_dt").dt.year().cast(pl.Int32).alias("anio"),
            pl.col("_fecha_dt").dt.month().cast(pl.Int32).alias("mes"),
        ])

        # 3. Franja horaria dominante del mes (opcional, enriquece el contexto)
        hora_col = _find_col(df.columns, HORA_COL_CANDIDATES)
        if hora_col:
            df = df.with_columns(
                pl.col(hora_col).str.extract(r"(\d+):", 1)
                .cast(pl.Int32, strict=False)
                .alias("_hora_int")
            ).with_columns(
                pl.when(pl.col("_hora_int").is_between(0, 5)).then(pl.lit("madrugada"))
                .when(pl.col("_hora_int").is_between(6, 11)).then(pl.lit("manana"))
                .when(pl.col("_hora_int").is_between(12, 17)).then(pl.lit("tarde"))
                .otherwise(pl.lit("noche"))
                .alias("franja_horaria")
            )

        # 4. Identificar columnas UPZ y tipo de delito
        upz_col  = _find_col(df.columns, UPZ_COL_CANDIDATES)
        tipo_col = _find_col(df.columns, TIPO_COL_CANDIDATES)

        if not upz_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna UPZ en F1 — verificar Bronze")

        # 5. Agregar por UPZ x mes
        group_cols = [upz_col, "anio", "mes"]
        agg_exprs  = [pl.len().alias("n_delitos")]

        if tipo_col:
            # tipo_delito_dominante = el tipo mas frecuente en esa UPZ ese mes
            agg_exprs.append(
                pl.col(tipo_col).drop_nulls().mode().first().alias("tipo_delito_dominante")
            )

        if hora_col:
            # franja dominante del mes
            agg_exprs.append(
                pl.col("franja_horaria").drop_nulls().mode().first().alias("franja_dominante_mes")
            )

        monthly = (
            df.group_by(group_cols)
            .agg(agg_exprs)
            .rename({upz_col: "upz_cod"})
            .with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
            .sort(["upz_cod", "anio", "mes"])
        )

        if verbose:
            print(f"    {len(monthly):,} filas UPZ x mes ({monthly['upz_cod'].n_unique()} UPZs, "
                  f"{monthly['anio'].min()}-{monthly['anio'].max()})")

        # 6. Lag features por UPZ
        # n_delitos_upz_4sem  ≈ delitos del mes anterior      (shift 1)
        # n_delitos_upz_8sem  ≈ delitos 2 meses anteriores acumulado (shift 1 + shift 2)
        monthly = monthly.with_columns([
            pl.col("n_delitos").shift(1).over("upz_cod").alias("n_delitos_upz_4sem"),
            (
                pl.col("n_delitos").shift(1).over("upz_cod") +
                pl.col("n_delitos").shift(2).over("upz_cod").fill_null(0)
            ).alias("n_delitos_upz_8sem"),
        ])

        monthly.write_parquet(out_path)
        rows = len(monthly)
        state.update(step, src_mtime=str(in_path.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} filas | {monthly['upz_cod'].n_unique()} UPZs | "
                               f"{monthly['anio'].min()}-{monthly['anio'].max()}")

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

    step     = "f3_clima"
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
    step     = "f7_estrato"
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
        gdf_manzanas = gpd.GeoDataFrame(
            df_estrato.to_pandas(),
            geometry=df_estrato["geometry_wkt"].to_pandas().apply(wkt.loads),
            crs="EPSG:4326",
        )
        # Usar centroide de la manzana para el join (mas rapido que interseccion de poligonos)
        gdf_manzanas["geometry"] = gdf_manzanas.geometry.centroid
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

        # Detectar columna codigo UPZ en el shapefile
        upz_id_col = _find_col(list(gdf_upz.columns),
                               ["UPZ", "upz", "COD_UPZ", "cod_upz", "CODIGO", "codigo"])
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna de codigo UPZ en F2")

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
    step     = "f4_cuadrantes"
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

        upz_id_col = _find_col(list(gdf_upz.columns),
                               ["UPZ", "upz", "COD_UPZ", "cod_upz", "CODIGO", "codigo"])
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna de codigo UPZ en F2")

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
    step     = "f8_transmilenio"
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

        upz_id_col = _find_col(list(gdf_upz.columns),
                               ["UPZ", "upz", "COD_UPZ", "cod_upz", "CODIGO", "codigo"])
        if not upz_id_col:
            return TransformResult(step, "error", 0, str(out_path),
                                   "No se encontro columna de codigo UPZ en F2")

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


# ─── Paso 6 — F5 NUSE → nuse_upz_mes.parquet ─────────────────────────────────

def transform_f5_nuse(
    state: TransformState,
    force: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> TransformResult:
    """
    Agrega incidentes NUSE 123 por UPZ x mes.
    El ratio NUSE/delitos se calcula en build_silver_table() cuando
    ya existe la tabla de delitos.

    Entrada:  datos/raw/f5_nuse_123.parquet
    Salida:   datos/procesados/nuse_upz_mes.parquet

    Columnas producidas:
        upz_cod, anio, mes, n_incidentes_nuse
    """
    import polars as pl

    step     = "f5_nuse"
    in_path  = RAW_DIR / "f5_nuse_123.parquet"
    out_path = PROC_DIR / "nuse_upz_mes.parquet"
    saved    = state.get(step)

    if not in_path.exists():
        return TransformResult(step, "error", 0, str(out_path),
                               "Bronze no disponible — correr: python src/pipeline.py --source f5")

    if not force and out_path.exists() and not _source_changed(in_path, saved):
        return TransformResult(step, "skipped", saved.get("rows_out", 0), str(out_path),
                               "NUSE sin cambios")

    if dry_run:
        return TransformResult(step, "updated", -1, str(out_path),
                               "[DRY-RUN] agregaria NUSE por UPZ x mes")

    try:
        df = pl.read_parquet(in_path)

        # Encontrar columnas clave
        upz_col   = _find_col(df.columns, ["COD_UPZ", "cod_upz", "UPZ", "upz"])
        anio_col  = _find_col(df.columns, ["ANIO", "anio", "AÑO", "año", "year"])
        mes_col   = _find_col(df.columns, ["MES", "mes", "month"])
        cant_col  = _find_col(df.columns, ["CANT_INCIDENTES", "cant_incidentes",
                                           "cantidad", "CANTIDAD", "count"])

        missing = [name for name, col in
                   [("UPZ", upz_col), ("ANIO", anio_col), ("MES", mes_col)]
                   if col is None]
        if missing:
            return TransformResult(step, "error", 0, str(out_path),
                                   f"Columnas no encontradas en F5: {missing}")

        # Normalizar codigo UPZ al formato "UPZnn" → solo numero
        df = df.with_columns(
            pl.col(upz_col).cast(pl.Utf8)
            .str.replace_all(r"[Uu][Pp][Zz]", "")
            .str.strip_chars()
            .alias("upz_cod")
        )

        group_cols = ["upz_cod", anio_col, mes_col]
        if cant_col:
            agg = pl.col(cant_col).cast(pl.Int64, strict=False).sum().alias("n_incidentes_nuse")
        else:
            agg = pl.len().alias("n_incidentes_nuse")

        result = (
            df.group_by(group_cols)
            .agg([agg])
            .rename({anio_col: "anio", mes_col: "mes"})
            .with_columns([
                pl.col("anio").cast(pl.Int32, strict=False),
                pl.col("mes").cast(pl.Int32, strict=False),
            ])
            .sort(["upz_cod", "anio", "mes"])
        )

        result.write_parquet(out_path)
        rows = len(result)
        if verbose:
            print(f"    {rows:,} filas | total incidentes: {result['n_incidentes_nuse'].sum():,}")
        state.update(step, src_mtime=str(in_path.stat().st_mtime), rows_out=rows,
                     file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} filas UPZ x mes | "
                               f"{result['n_incidentes_nuse'].sum():,} incidentes totales")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


# ─── Paso 7 — Tabla Silver final → delitos_por_upz_mes.parquet ───────────────

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

    Entrada:  datos/procesados/delitos_upz_mes.parquet
              datos/procesados/clima_diario.parquet
              datos/procesados/nuse_upz_mes.parquet
              datos/procesados/estrato_por_upz.csv
              datos/procesados/features_cuadrantes_upz.csv
              datos/procesados/features_tm_upz.csv
    Salida:   datos/procesados/silver_upz_mes.parquet

    Esta tabla tiene TODAS las variables candidatas.
    La capa Gold (Notebook 03) decide cuales entran al modelo.
    """
    import polars as pl

    step     = "silver_table"
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
        cuad     = pl.read_csv(required["features_cuadrantes_upz"])
        tm       = pl.read_csv(required["tm"])

        # Estandarizar tipos de upz_cod en todas las tablas
        for df_name, df in [("estrato", estrato), ("cuad", cuad), ("tm", tm)]:
            pass  # ya son pl.DataFrame de read_csv, upz_cod es Utf8

        # Asegurar upz_cod como string en base
        base = base.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())

        # JOIN 1: agregar clima mensual promedio (temperatura y lluvia del mes)
        clima_mensual = clima.group_by(["anio", "mes"]).agg([
            pl.col("temperatura_c").mean().round(2).alias("temperatura_c"),
            pl.col("precipitacion_mm").sum().round(2).alias("precipitacion_mm_mes"),
        ])
        silver = base.join(clima_mensual, on=["anio", "mes"], how="left")

        # JOIN 2: NUSE → calcular ratio_nuse_delitos_upz
        nuse = nuse.with_columns(pl.col("upz_cod").cast(pl.Utf8).str.strip_chars())
        silver = silver.join(nuse, on=["upz_cod", "anio", "mes"], how="left")
        silver = silver.with_columns(
            pl.when(pl.col("n_delitos") > 0)
            .then(pl.col("n_incidentes_nuse") / pl.col("n_delitos"))
            .otherwise(pl.lit(0.0))
            .round(4)
            .alias("ratio_nuse_delitos_upz")
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

        silver = silver.sort(["upz_cod", "anio", "mes"])
        silver.write_parquet(out_path)
        rows = len(silver)

        if verbose:
            print(f"    {rows:,} filas | {silver['upz_cod'].n_unique()} UPZs | "
                  f"{silver.columns} columnas")
            nulls = {c: silver[c].null_count() for c in silver.columns if silver[c].null_count() > 0}
            if nulls:
                print(f"    Nulls por columna: {nulls}")

        state.update(step, rows_out=rows, columns=silver.columns, file_path=str(out_path))
        return TransformResult(step, "updated", rows, str(out_path),
                               f"{rows:,} filas | {len(silver.columns)} columnas | "
                               f"{silver['upz_cod'].n_unique()} UPZs")

    except Exception as exc:
        return TransformResult(step, "error", 0, str(out_path), str(exc))


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
    "f1":    "F1 Delitos -> UPZ x mes",
    "f3":    "F3 Clima -> diario",
    "f4":    "F4 Cuadrantes -> features UPZ",
    "f5":    "F5 NUSE -> UPZ x mes",
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
