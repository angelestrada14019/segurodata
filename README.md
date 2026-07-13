# SeguroData Bogotá
### Concurso Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana

> Sistema de predicción y prescripción de crimen urbano para Bogotá D.C.
> construido sobre datos abiertos, XGBoost y OpenRouter.

**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Concurso:** Datos al Ecosistema 2026 — MinTIC · Reto #2 Seguridad Ciudadana · Nivel Medio  
**Entrega:** 13 julio 2026 · GitHub público + registro en datos.gov.co

📊 **[Diagrama de arquitectura de fuentes](docs/diagrama_arquitectura.svg)**

---

## Producción

| Componente | URL |
|---|---|
| **Frontend** (React + deck.gl) | https://segurodata-frontend.vercel.app |
| **Backend** (FastAPI) | https://segurodata-api-production.up.railway.app |
| **Docs API** | https://segurodata-api-production.up.railway.app/docs |

Los 4 módulos (Diagnóstico · Predicción · Prescriptivo · Chatbot causal) + Panel Admin están
desplegados y funcionando con datos reales.

---

## Arquitectura Medallion

```
Bronze  datos/raw/          src/pipeline.py   ← extraccion incremental — 12 fuentes (F1-F8 + F10 corpus + F11/F13/F14 nuevas)  ✅
Silver  datos/procesados/   src/transform.py  ← limpieza, joins, agrega por UPZ   ✅
Gold    datos/features/     train_model.py    ← 18 variables + tabla maestra        ✅
Model   datos/modelos/      train_model.py    ← XGBoost entrenado + SHAP values    ✅
```

---

## Las 12 fuentes de datos

Todas públicas y gratuitas — **~870,000 registros Bronze en total**:

| # | Fuente | Filas (Bronze) | Granularidad | Contribución a Silver | Actualización |
|---|--------|---------------:|--------------|----------------------|--------------|
| F1 | Delito de Alto Impacto — Sec. Seguridad | 21 | Localidad × año | EDA histórico 2018–2026 + ruptures (cambios estructurales) | Semestral |
| F2 | UPZ Shapefile — IDECA | 112 | UPZ (polígono) | Base espacial para spatial joins | Estático |
| F3 | Clima Bogotá — Open-Meteo | 56,112 | Hora | +2 cols: `temperatura_c`, `precipitacion_mm_mes` | Diaria |
| F4 | Cuadrantes de Policía — MEBOG | 599 | Cuadrante (polígono) | +2 cols: `cuadrantes_por_km2`, CAI | Anual |
| **F5** | **Incidentes NUSE 123 — C4** | **128,314** | **UPZ × mes × tipo (86 tipos)** | **Base de filas** → 111,606 rows silver | Mensual |
| F6 | Hurto a Personas — Policía Nacional | 638,569 | Municipio × día | Benchmarking nacional (sin desglose UPZ) | Mensual |
| F7 | Estratificación por manzana — SDP | 44,260 | Manzana (polígono) | +1 col: `estrato_promedio_upz` | Según necesidad |
| F8 | Estaciones TransMilenio — TM S.A. | 153 | Estación (punto) | +2 cols: `dist_tm_metros`, `n_estaciones_tm` | Estático |
| F10 | Noticias RSS — El Tiempo / Espectador / El Informante Soy Yo | N/A (texto) | Artículo (3 feeds verificados) | Corpus GraphRAG → Supabase pgvector | Diaria |
| **F11** | **Malla Vial + Obras IDU** | ~miles | Segmento vial | +1 col: `km_via_intervenida_upz` | Mensual |
| **F13** | **Cámaras Salvavidas SDM** | 92 | Punto (cámara) | +1 col: `n_camaras_upz` + capa deck.gl | Semestral |
| **F14** | **Alumbrado Público UAESP** | 112 | UPZ (directo) | +1 col: `luminarias_led_upz` | Anual |
| | **TOTAL BRONZE** | **~870,000+** | | **Silver: 111,606 × 20 cols** | |

> **¿Por qué ~870K Bronze → 111K Silver?**
>
> La tabla Silver tiene una fila por cada combinación **UPZ × mes × tipo\_de\_incidente** — esas filas vienen de F5 NUSE, el único archivo con las tres dimensiones juntas. Las otras fuentes no crean filas nuevas: **F3 agrega columnas** de clima por mes, **F4/F7/F8/F11/F13/F14 agregan columnas** de características de la UPZ (cuadrantes, estrato, TM, obras, cámaras, luminarias). F2 es la base geométrica para los spatial joins. F1 (granularidad localidad) y F6 (granularidad municipio) no tienen desglose UPZ y se usan como referencia de contexto.
>
> La columna `es_crimen` en Silver distingue los 19 tipos de alto impacto criminal (HURTO, RIÑA, LESIONES…) del resto (RUIDO, ACCIDENTE TRÁNSITO, EMBRIAGUEZ…).
>
> **F10 (RSS noticias)** no entra en XGBoost — es corpus de texto para los Módulos 3 (Prescriptivo) y 4 (Chatbot causal) vía GraphRAG + OpenRouter.

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

Descarga las 12 fuentes de forma **incremental**: compara el estado local contra el servidor y solo descarga si hay datos nuevos. Segunda ejecución del mismo día → instantánea.

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
delitos  = pl.read_parquet("datos/raw/f1_delito_alto_impacto.parquet")
upz      = gpd.read_file("datos/raw/f2_upz.geojson")
clima    = pl.read_parquet("datos/raw/f3_clima_bogota.parquet")
nuse     = pl.read_parquet("datos/raw/f5_nuse_123.parquet")
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
Ver [Wiki — Transformacion](https://github.com/angelestrada14019/segurodata/wiki/Transformacion) para instrucciones completas.

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
| f1 | `f1_delito_alto_impacto.parquet` | `delitos_localidad_anio.parquet` | DAI por localidad × año (referencia EDA) |
| f3 | `f3_clima_bogota.parquet` | `clima_diario.parquet` | Horario → diario |
| f4 | `f4_cuadrantes.geojson` | `features_cuadrantes_upz.csv` | Spatial join → cuadrantes/km² |
| f5 | `f5_nuse_123.parquet` | `delitos_upz_mes.parquet` + `nuse_upz_mes.parquet` | NUSE por UPZ × mes + lags (base del modelo) |
| f7 | `f7_estratificacion.parquet` | `estrato_por_upz.csv` | Spatial join manzanas → estrato promedio UPZ ⚠️ pesado |
| f8 | `f8_transmilenio.geojson` | `features_tm_upz.csv` | Distancia y conteo TM por UPZ |
| silver | todos los anteriores | `silver_upz_mes.parquet` | Tabla final unida (20 columnas, 111,606 filas) |

> ⚠️ El paso `f7` (estratificación) carga ~115K polígonos. En Colab gratuito puede agotar RAM — ver [Wiki — Transformacion](https://github.com/angelestrada14019/segurodata/wiki/Transformacion) para alternativas.

---

## Estructura del repositorio

```
segurodata/
├── datos/
│   ├── raw/              <- Bronze: archivos originales (generados por pipeline.py)
│   ├── procesados/       <- Silver: datos limpios por UPZ (generados por transform.py)
│   ├── features/         <- Gold:   tabla maestra 18 variables (train_model.py)
│   ├── grafo/            <- GraphRAG: embeddings pgvector — sentence-transformers (Fase 3)
│   └── modelos/          <- Model:  XGBoost + SHAP (train_model.py)
├── graficas/             <- Gráficas del análisis exploratorio (ver wiki — Analisis-Exploratorio)
├── src/
│   ├── etl.py            <- Conectores de bajo nivel: CKAN, Socrata, ArcGIS, Open-Meteo
│   ├── pipeline.py       <- Extracción incremental Bronze (12 fuentes activas)
│   ├── transform.py      <- Transformación Silver (limpieza + spatial joins)
│   └── validar_fuentes.py
├── .github/
│   └── workflows/
│       └── etl-semanal.yml  <- pipeline+reentrenamiento con quality-gate (schedule desactivado)
├── docs/
│   ├── diagrama_arquitectura.svg <- Diagrama visual de la arquitectura (abre en browser)
│   └── fuentes_validadas.xlsx    <- Excel de 20 fuentes validadas (4 hojas)
├── wiki_pages/           <- FUENTE ÚNICA de documentación → PUSH_WIKI.bat → GitHub wiki
│   ├── Home.md / Fuentes-de-Datos.md / Arquitectura.md / Modulos.md / Metodologia.md
│   ├── Replicacion.md / Instalacion.md / Transformacion.md / Estado-del-Arte.md
│   ├── Provenance.md / Investigacion-Fuentes.md / Reglas-Concurso.md / Analisis-Exploratorio.md
│   └── PUSH_WIKI.bat     <- helper para publicar el wiki
├── .env.example          <- Template de variables de entorno
├── .gitignore
├── CLAUDE.md             <- contexto para sesiones de IA
├── CRONOGRAMA.md         <- checklists de tareas por fase
├── requirements.txt
└── README.md
```

> Los datos (`datos/raw/`, `datos/procesados/`, etc.) no se suben al repo — se generan localmente ejecutando `pipeline.py` y `transform.py`.

---

## Automatización (GitHub Actions)

`.github/workflows/etl-semanal.yml` corre la cadena completa bajo demanda — descarga incremental →
Silver → reentrena XGBoost (split temporal dinámico) → quality-gate de métricas → carga a Supabase
(solo si el modelo nuevo no es peor que el anterior). Probado de punta a punta en CI real. El
`schedule` semanal queda **desactivado a propósito** hasta después de la sustentación oral — se
dispara manualmente desde **GitHub → Actions → `etl-semanal.yml` → Run workflow**. Detalles y
secrets requeridos en el [Wiki — Instalación](https://github.com/angelestrada14019/segurodata/wiki/Instalacion#6-github-actions--pipeline-de-reentrenamiento-opcional-ya-probado-en-ci-real).

---

## Stack tecnológico

```
Ingesta          polars · requests · geopandas · python-dotenv
Transformación   geopandas · shapely · polars
Modelado         xgboost · scikit-learn · shap · ruptures
Embeddings       sentence-transformers (all-MiniLM-L6-v2, local, sin costo de API)
GraphRAG         FastAPI (Python) — pgvector + OpenRouter
LLM              OpenRouter (google/gemini-2.5-flash-lite por defecto — costo marginal)
Base de datos    Supabase (PostgreSQL + PostGIS + pgvector)
Frontend / mapa  React + Vite + deck.gl + Tailwind CSS → Vercel
Backend ML       Railway (FastAPI — siempre activo, sin cold start, ~$5/mes)
```

---

## Metodología CRISP-ML

El proceso CRISP-ML completo queda documentado en el [Wiki](https://github.com/angelestrada14019/segurodata/wiki) y ejecutado en scripts versionados:

| Fase | Contenido | Dónde vive |
|------|-----------|-----------|
| Plan + fuentes | Catálogo de 12 fuentes activas + F12 planificada, arquitectura | [Wiki — Fuentes-de-Datos](https://github.com/angelestrada14019/segurodata/wiki/Fuentes-de-Datos), [Wiki — Provenance](https://github.com/angelestrada14019/segurodata/wiki/Provenance) |
| Análisis exploratorio | Distribución espacial y temporal del riesgo, change points `ruptures` | [Wiki — Analisis-Exploratorio](https://github.com/angelestrada14019/segurodata/wiki/Analisis-Exploratorio) |
| Features + modelo | 18 variables, XGBoost, SHAP pre-computado, análisis de sesgo, tabla ontológica prescriptiva | `scripts/train_model.py` — ejecutado, ver `datos/modelos/metricas.json` |
| Arquitectura + deploy | React+FastAPI+Supabase, Vercel + Railway | [Wiki — Arquitectura](https://github.com/angelestrada14019/segurodata/wiki/Arquitectura), [Wiki — Instalacion](https://github.com/angelestrada14019/segurodata/wiki/Instalacion) |

---

## Documentación

📖 **[Documentación completa en el Wiki](https://github.com/angelestrada14019/segurodata/wiki)**

El wiki incluye: catálogo de 20 fuentes · estado del arte internacional · guía capa Silver · provenance de datos · reglas del concurso y preguntas del jurado.

| Código | Ubicación | Para qué |
|--------|----------|---------|
| Conectores ETL | `src/etl.py` | CKAN, Socrata, ArcGIS, Open-Meteo de bajo nivel |
| Pipeline Bronze | `src/pipeline.py` | Extracción incremental de las 12 fuentes |
| Pipeline Silver | `src/transform.py` | Limpieza, joins espaciales, tabla silver |
| Excel fuentes validadas | `docs/fuentes_validadas.xlsx` | Metadatos, URLs, estado de cada fuente |
