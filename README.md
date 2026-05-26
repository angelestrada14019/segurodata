# SeguroData Bogotá — Capa de Extracción (Bronze)
### Concurso Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana

> Pipeline de extracción incremental de 8 fuentes de datos abiertos de Bogotá D.C.
> Arquitectura Medallion: este repositorio cubre la capa **Bronze** (datos en crudo).

---

## Contexto del proyecto

SeguroData Bogotá es un sistema de predicción y prescripción de crimen urbano para Bogotá D.C. construido sobre datos abiertos. El proyecto sigue una arquitectura Medallion con responsabilidades separadas por capa:

```
Bronze  ← este repo    Extracción y descarga de las 8 fuentes originales
Silver  ← siguiente    Limpieza, joins espaciales y agregación por UPZ
Gold    ← siguiente    Tabla maestra con las 14 variables del modelo
Model   ← siguiente    XGBoost entrenado + SHAP values
```

**Esta capa (Bronze)** se encarga de conectar con los portales de datos abiertos, detectar actualizaciones y guardar los archivos originales en `datos/raw/` sin transformar.

---

## Las 8 fuentes de datos

Todas son públicas y gratuitas:

| # | Fuente | Portal | Frecuencia de actualización |
|---|--------|--------|-----------------------------|
| F1 | Delito de Alto Impacto — Sec. Seguridad | datosabiertos.bogota.gov.co | Semestral |
| F2 | UPZ Shapefile — IDECA | datosabiertos.bogota.gov.co | Estático |
| F3 | Clima Bogotá — Open-Meteo | open-meteo.com | Diaria |
| F4 | Cuadrantes de Policía — MEBOG | datosabiertos.bogota.gov.co | Anual |
| F5 | Incidentes NUSE 123 — C4 | datosabiertos.bogota.gov.co | Mensual |
| F6 | Hurto a Personas — Policía Nacional | datos.gov.co | Mensual |
| F7 | Estratificación por manzana — SDP | datosabiertos.bogota.gov.co | Según necesidad |
| F8 | Estaciones TransMilenio — TM S.A. | datosabiertos.bogota.gov.co | Estático |

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/segurodata-bogota.git
cd segurodata-bogota

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux / Mac
.venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Token Socrata para mayor cuota en F6
cp .env.example .env
# Editar .env: SOCRATA_APP_TOKEN=tu_token
# Token gratis en: https://dev.socrata.com/register
```

### En Google Colab

```python
!git clone https://github.com/tu-usuario/segurodata-bogota.git
%cd segurodata-bogota
!pip install -r requirements.txt -q
```

---

## Uso del pipeline (`src/pipeline.py`)

El pipeline descarga cada fuente de forma **incremental**: compara el estado local contra el servidor y solo descarga si hay datos nuevos. La segunda ejecución del mismo día es instantánea.

### Comandos

```bash
# Ver qué descargaría SIN ejecutar nada
python src/pipeline.py --dry-run

# Ver estado actual de todas las fuentes
python src/pipeline.py --status

# Descargar todo (solo lo nuevo)
python src/pipeline.py

# Descargar una fuente específica con detalle de progreso
python src/pipeline.py --source f3 --verbose

# Varias fuentes a la vez
python src/pipeline.py --source f1 f2 f8

# Forzar re-descarga aunque no haya cambios
python src/pipeline.py --source f1 --force
```

### Ejemplo de salida

```
------------------------------------------------------------
  SeguroData Bogota - Pipeline de extraccion (Bronze layer)
------------------------------------------------------------
[OK] f1_delitos          updated  new= 587,234  total= 587,234  587,234 filas — validacion OK
[OK] f2_upz              updated  new=     112  total=     112  112 filas — validacion OK
[OK] f3_clima            updated  new=  56,064  total=  56,064  append 2020-01-01->2026-05-24
[--] f4_cuadrantes       skipped  new=       0  total=   4,821  Last-Modified sin cambios
[OK] f5_nuse             updated  new= 124,000  total=1,240,000 validacion OK
[--] f7_estratificacion  skipped  new=       0  total= 115,430  estratificacion sin cambios

------------------------------------------------------------
  Resumen: 4 actualizadas  2 sin cambios  0 errores
------------------------------------------------------------
```

### Desde un notebook o script Python

```python
from src.pipeline import run_pipeline, extract_f3_clima, PipelineState

# Correr todas las fuentes
resultados = run_pipeline(verbose=True)

# Correr solo una fuente
state = PipelineState()
result = extract_f3_clima(state, verbose=True)
print(result.status, result.rows_new, result.message)

# Leer los archivos descargados
import polars as pl
import geopandas as gpd

delitos = pl.read_parquet("datos/raw/f1_delito_alto_impacto.parquet")
upz     = gpd.read_file("datos/raw/f2_upz.geojson")
clima   = pl.read_parquet("datos/raw/f3_clima_bogota.parquet")
```

### Lógica incremental por fuente

| Fuente | Estrategia |
|--------|-----------|
| F1, F2, F4, F7 | HTTP `Last-Modified` — descarga solo si el servidor cambió el archivo |
| F3 Clima | Append desde `max(fecha)` del Parquet existente hasta ayer |
| F5 NUSE | Descarga por año (CKAN no soporta filtros `>=`) y deduplica |
| F6 Hurto PN | Socrata `$where fecha_hecho > 'max_fecha'` |
| F8 TransMilenio | CKAN `package_show` → compara `metadata_modified` |

El estado de cada fuente se guarda automáticamente en `datos/raw/.pipeline_state.json`.

---

## Archivos generados en `datos/raw/`

| Archivo | Fuente | Formato | Notas |
|---------|--------|---------|-------|
| `f1_delito_alto_impacto.parquet` | F1 | Parquet | geometry como columna WKT |
| `f1_delito_alto_impacto.zip` | F1 | ZIP | backup del original |
| `f2_upz.geojson` | F2 | GeoJSON | 112 polígonos UPZ |
| `f3_clima_bogota.parquet` | F3 | Parquet | horario 2020→hoy |
| `f4_cuadrantes.geojson` | F4 | GeoJSON | cuadrantes policiales |
| `f4_cuadrantes.zip` | F4 | ZIP | backup del original |
| `f5_nuse_123.parquet` | F5 | Parquet | incidentes NUSE |
| `f6_hurto_personas.parquet` | F6 | Parquet | hurtos Policía Nacional |
| `f7_estratificacion.parquet` | F7 | Parquet | ~115K manzanas con WKT |
| `f8_transmilenio.geojson` | F8 | GeoJSON | estaciones TM |
| `.pipeline_state.json` | — | JSON | estado de cada fuente |

---

## Estructura del repositorio

```
segurodata-bogota/
├── datos/
│   ├── raw/              <- Bronze: archivos originales descargados
│   ├── procesados/       <- Silver: (capa siguiente — transformación)
│   ├── features/         <- Gold:   (capa siguiente — feature engineering)
│   └── modelos/          <- Model:  (capa siguiente — XGBoost entrenado)
├── src/
│   ├── etl.py            <- Conectores de bajo nivel: CKAN, Socrata, ArcGIS, Open-Meteo
│   └── pipeline.py       <- Orquestador incremental de las 8 fuentes
├── .github/
│   └── workflows/
│       └── etl-semanal.yml  <- GitHub Action (desactivado — ver sección Automatización)
├── docs/
│   ├── ESTADO_DEL_ARTE.md
│   ├── INVESTIGACION_FUENTES.md
│   └── fuentes_validadas.xlsx
├── SeguroData_01_Plan_y_Fuentes.ipynb  <- Notebook de planificación
├── CLAUDE.md
├── PROYECTO.md
├── CRONOGRAMA.md
├── REGLAS.md
├── requirements.txt
└── README.md
```

---

## Automatización con GitHub Actions

El archivo `.github/workflows/etl-semanal.yml` está creado pero **desactivado**.

Cuando se quiera activar:
1. Abrir `.github/workflows/etl-semanal.yml`
2. Descomentar el bloque `schedule`:
   ```yaml
   schedule:
     - cron: '0 6 * * 1'   # cada lunes a las 6am UTC
   ```
3. Hacer commit — GitHub lo activará automáticamente

También se puede lanzar manualmente desde **GitHub → Actions → ETL semanal → Run workflow** sin necesidad de activar el schedule.

**Qué automatiza:** descarga incremental de F3 (clima, diaria), F5 (NUSE, mensual) y F6 (Hurto PN, mensual). Las fuentes semestrales o estáticas (F1, F2, F4, F7, F8) se descargan manualmente cuando sea necesario.

**Requiere:** agregar `SOCRATA_APP_TOKEN` como secreto en GitHub → Settings → Secrets (opcional pero recomendado para F6).

---

## Dependencias principales

```
polars          # DataFrames rápidos para datos tabulares
geopandas       # Datos espaciales (GeoJSON, shapefiles)
requests        # Llamadas HTTP a las APIs
python-dotenv   # Variables de entorno (.env)
```

Ver `requirements.txt` para la lista completa.

---

## Concurso

**Datos al Ecosistema 2026** — MinTIC · Reto #2 Seguridad Ciudadana y Justicia · Nivel Medio  
Entrega: 13 julio 2026 · GitHub público + registro en datos.gov.co
