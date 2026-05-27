# SeguroData Bogotá
### Concurso Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana

> Sistema de predicción y prescripción de crimen urbano para Bogotá D.C.
> construido sobre datos abiertos, XGBoost y Claude API.

**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Concurso:** Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana · Nivel Medio  
**Entrega:** 13 julio 2026 · GitHub público + registro en datos.gov.co

---

## Estructura de ramas

El proyecto está organizado por capas, cada una en su propia rama:

| Rama | Capa | Responsable | Estado |
|------|------|-------------|--------|
| `main` | Integración | Todos (via PR) | ✅ Activa |
| `bronze` | Extracción de datos | Equipo A | ✅ Completo |
| `silver` | Transformación y limpieza | Equipo B | 🔄 En curso |
| `gold` | Feature engineering | — | ⏳ Pendiente |
| `model` | XGBoost + SHAP | — | ⏳ Pendiente |
| `dashboard` | Streamlit + Claude API | — | ⏳ Pendiente |

**Flujo:** cada equipo trabaja en su rama → Pull Request a `main` cuando esté listo → `main` siempre ejecutable.

---

## Arquitectura Medallion

```
Bronze  datos/raw/          src/pipeline.py   ← extraccion incremental 8 fuentes  ✅
Silver  datos/procesados/   src/transform.py  ← limpieza, joins, agrega por UPZ   🔄
Gold    datos/features/     Notebook 03       ← 14 variables + tabla maestra       ⏳
Model   datos/modelos/      Notebook 04       ← XGBoost entrenado + SHAP values    ⏳
```

---

## Las 8 fuentes de datos

Todas públicas y gratuitas:

| # | Fuente | Portal | Actualización |
|---|--------|--------|--------------|
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
git clone https://github.com/angelestrada14019/segurodata.git
cd segurodata

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux / Mac
.venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus tokens (ver .env.example)
```

### En Google Colab

```python
!git clone https://github.com/angelestrada14019/segurodata.git
%cd segurodata
!pip install -r requirements.txt -q
```

---

## Bronze — Extracción (`src/pipeline.py`)

Descarga las 8 fuentes de forma **incremental**: compara el estado local contra el servidor y solo descarga si hay datos nuevos. Segunda ejecución del mismo día → instantánea.

```bash
python src/pipeline.py --dry-run          # ver qué descargaría sin ejecutar
python src/pipeline.py --status           # estado de todas las fuentes
python src/pipeline.py                    # descargar todo (solo lo nuevo)
python src/pipeline.py --source f3        # fuente específica
python src/pipeline.py --source f1 --force  # forzar re-descarga
```

```python
# Desde notebook
from src.pipeline import run_pipeline
resultados = run_pipeline(verbose=True)

import polars as pl, geopandas as gpd
delitos = pl.read_parquet("datos/raw/f1_delito_alto_impacto.parquet")
upz     = gpd.read_file("datos/raw/f2_upz.geojson")
clima   = pl.read_parquet("datos/raw/f3_clima_bogota.parquet")
```

| Fuente | Estrategia incremental |
|--------|----------------------|
| F1, F2, F4, F7 | HTTP `Last-Modified` — solo descarga si el servidor cambió |
| F3 Clima | Append desde `max(fecha)` hasta ayer |
| F5 NUSE | Descarga por año y deduplica |
| F6 Hurto PN | Socrata `$where fecha_hecho > 'max_fecha'` |
| F8 TransMilenio | CKAN `package_show` → compara `metadata_modified` |

---

## Silver — Transformación (`src/transform.py`)

Toma los archivos Bronze y produce una tabla limpia agregada por **UPZ × mes**.  
Ver `docs/TRANSFORMACION.md` para instrucciones completas.

```bash
python src/transform.py --dry-run         # ver qué transformaría sin ejecutar
python src/transform.py --status          # estado de cada paso
python src/transform.py                   # correr todos los pasos
python src/transform.py --step f1 f3      # pasos específicos
python src/transform.py --step f7 --force # forzar re-cálculo (paso pesado)
```

```python
# Desde notebook
from src.transform import run_transform
resultados = run_transform(verbose=True)

silver = pl.read_parquet("datos/procesados/silver_upz_mes.parquet")
```

**Pasos del transform:**

| Paso | Entrada | Salida | Descripción |
|------|---------|--------|-------------|
| f1 | `f1_delito_alto_impacto.parquet` | `delitos_upz_mes.parquet` | Agrega crimen por UPZ × mes + lags |
| f3 | `f3_clima_bogota.parquet` | `clima_diario.parquet` | Horario → diario |
| f4 | `f4_cuadrantes.geojson` | `features_cuadrantes_upz.csv` | Spatial join → cuadrantes/km² |
| f5 | `f5_nuse_123.parquet` | `nuse_upz_mes.parquet` | Agrega NUSE por UPZ × mes |
| f7 | `f7_estratificacion.parquet` | `estrato_por_upz.csv` | Spatial join ~115K manzanas ⚠️ pesado |
| f8 | `f8_transmilenio.geojson` | `features_tm_upz.csv` | Distancia y conteo TM por UPZ |
| silver | todos los anteriores | `silver_upz_mes.parquet` | Tabla final unida (18 columnas) |

> ⚠️ El paso `f7` (estratificación) carga ~115K polígonos. En Colab gratuito puede agotar RAM — ver `docs/TRANSFORMACION.md` para alternativas.

---

## Estructura del repositorio

```
segurodata/
├── datos/
│   ├── raw/              <- Bronze: archivos originales (generados por pipeline.py)
│   ├── procesados/       <- Silver: datos limpios por UPZ (generados por transform.py)
│   ├── features/         <- Gold:   tabla maestra 14 variables (Notebook 03)
│   └── modelos/          <- Model:  XGBoost + SHAP (Notebook 04)
├── graficas/             <- Outputs del EDA
├── src/
│   ├── etl.py            <- Conectores de bajo nivel: CKAN, Socrata, ArcGIS, Open-Meteo
│   ├── pipeline.py       <- Extracción incremental Bronze (8 fuentes)
│   ├── transform.py      <- Transformación Silver (limpieza + spatial joins)
│   └── validar_fuentes.py
├── .github/
│   └── workflows/
│       └── etl-semanal.yml  <- GitHub Action (desactivado — activar descomentando schedule)
├── docs/
│   ├── TRANSFORMACION.md    <- Instrucciones completas para la capa Silver
│   ├── ESTADO_DEL_ARTE.md   <- 20+ sistemas internacionales, 18 papers
│   ├── INVESTIGACION_FUENTES.md
│   └── fuentes_validadas.xlsx
├── SeguroData_01_Plan_y_Fuentes.ipynb
├── .env.example          <- Template de variables de entorno
├── .gitignore
├── CLAUDE.md
├── PROYECTO.md
├── CRONOGRAMA.md
├── REGLAS.md
├── requirements.txt
└── README.md
```

> Los datos (`datos/raw/`, `datos/procesados/`, etc.) no se suben al repo — se generan localmente ejecutando `pipeline.py` y `transform.py`.

---

## Automatización (GitHub Actions)

El archivo `.github/workflows/etl-semanal.yml` está **desactivado**. Para activarlo:

1. Descomentar el bloque `schedule` en el archivo
2. Agregar `SOCRATA_APP_TOKEN` en GitHub → Settings → Secrets
3. Hacer commit → GitHub activa el cron automáticamente

También ejecutable manualmente: **GitHub → Actions → ETL semanal → Run workflow**.

---

## Stack tecnológico

```
Ingesta          polars · requests · geopandas · python-dotenv
Transformación   geopandas · shapely · polars
Modelado         xgboost · scikit-learn · shap
IA Generativa    anthropic (Claude API) — Módulos 3 y 4 únicamente
Dashboard        streamlit · plotly · folium
```

---

## Notebooks CRISP-ML

| Notebook | Fase | Contenido | Estado |
|----------|------|-----------|--------|
| `SeguroData_01_Plan_y_Fuentes.ipynb` | 0 | Plan + catálogo de 8 fuentes | ✅ |
| `SeguroData_02_EDA.ipynb` | 1 | Análisis exploratorio | ⏳ |
| `SeguroData_03_Features.ipynb` | 2 | 14 variables + correlación | ⏳ |
| `SeguroData_04_Modelo.ipynb` | 2 | XGBoost + SHAP + sesgo | ⏳ |
| `SeguroData_05_Dashboard.ipynb` | 3 | Streamlit + Claude API | ⏳ |
| `SeguroData_06_Deployment.ipynb` | 4 | Deploy + docs + video | ⏳ |
