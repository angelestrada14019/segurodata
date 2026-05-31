# CRONOGRAMA.md — Fases del Proyecto SeguroData Bogotá

> Entrega: **13 julio 2026** (GitHub público + registro datos.gov.co) · Sustentación: 14–17 julio
>
> **Nota sobre fecha:** Existe posibilidad de que el evento final sea GovCamps agosto 2026. Si se confirma, hay ~3 semanas extra. Verificar en datos.gov.co antes de la Fase 4.

---

## Vista general

```
MAYO                        JUNIO                          JULIO
Fase 0 ✅ | Fase 1A ✅ | Fase 1B ✅ | Fase 2 ⏳ | Fase 3 ⏳ | Fase 4 ⏳
25 May    | 26–27 May  | 27M–6Jun   |  7–20 Jun | 21J–10Jul | 11–13 Jul
[Plan]    | [Bronze]   | [Silver+EDA]| [Modelo]  | [Dashboard+IA] | [Docs]
```

**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Ramas activas:** `main` · `bronze` ✅ · `silver` 🔄 · `gold` · `model` · `dashboard`

---

## Fase 0 ✅ — Completada (23 mayo 2026)

**Entregable:** `SeguroData_01_Plan_y_Fuentes.ipynb`

- ✅ Descripción del problema y propuesta
- ✅ 3 perfiles de usuario definidos (Comandante CAI, Sec. Seguridad, Ciudadano)
- ✅ 4 módulos del sistema definidos (Diagnóstico, Predicción, Recomendación, Chatbot)
- ✅ Catálogo de 12 fuentes (F1-F10 activas + F11/F12 planificadas) con URLs verificadas, variables y código de carga
- ✅ Arquitectura Medallón definida (Bronze/Silver/Gold/Model)
- ✅ 14 variables del modelo XGBoost documentadas
- ✅ Cronograma de fases con fechas
- ✅ Criterios de evaluación del concurso con puntaje estimado (87/100)
- ✅ Scripts ETL en `src/etl.py` (CKAN, Socrata, ArcGIS, Open-Meteo)
- ✅ Catálogo ampliado de 20 fuentes en `docs/` (investigación de referencia)

---

## Fase 1A ✅ — Bronze layer (26–27 mayo 2026)

**Entregable:** `src/pipeline.py` + `src/etl.py` — extracción incremental lista

- ✅ `src/etl.py` — conectores CKAN, Socrata, ArcGIS, Open-Meteo + `get_last_modified()`
- ✅ `src/pipeline.py` — 10 extractores con lógica incremental (F1-F8 estructurados + F9/F10 corpus LLM)
- ✅ `PipelineState` — estado persistente en `.pipeline_state.json`
- ✅ CLI: `--dry-run`, `--status`, `--source`, `--force`, `--verbose`
- ✅ GitHub: rama `bronze` publicada + `main` con commit inicial
- ✅ Probado: F3 descargó 56,064 filas · segunda ejecución → skip instantáneo
- ✅ GitHub Action `etl-semanal.yml` creado (desactivado hasta Fase 3)

---

## Fase 1B ✅ — Silver layer + EDA (27 mayo – 6 junio 2026)

**Entregables:**
- `src/transform.py` — pipeline Silver (rama `silver`) ✅
- `SeguroData_02_EDA.ipynb` — análisis exploratorio completo ✅

### Semana 1 (26 mayo – 1 junio) — Descarga y limpieza

> ✅ La descarga ya está automatizada — usar `python src/pipeline.py` en lugar de los pasos manuales de abajo.

**FUENTE 1 — Delito de Alto Impacto (ZIP GeoJSON):**
- [x] `python src/pipeline.py --source f1` → `datos/raw/f1_delito_alto_impacto.parquet`
- [x] Verificar columnas en EDA — F1 es agregado por localidad×año (21 localidades, 2018–2026), no UPZ
- [x] `python src/transform.py --step f1` → `datos/procesados/delitos_localidad_anio.parquet` (2,079 filas, referencia EDA)

**FUENTE 2 — UPZ Shapefile:**
- [x] `python src/pipeline.py --source f2` → `datos/raw/f2_upz.geojson`
- [x] Verificado N=112 polígonos, CRS EPSG:4326, columna `CODIGO_UPZ`
- [x] Explorar columnas: `CODIGO_UPZ`, `NOMBRE`, `AREA_HECTAREAS` — base espacial para spatial joins
- _Nota: F2 no tiene paso transform propio — es referencia espacial usada en los spatial joins de F4, F7 y F8._

**FUENTE 3 — Open-Meteo:**
- [x] `python src/pipeline.py --source f3` → `datos/raw/f3_clima_bogota.parquet` (descarga incremental desde `max(fecha)`)
- [x] `python src/transform.py --step f3` → `datos/procesados/clima_diario.parquet` (2,338 días)
- [x] Verificado columnas: `temperatura_c`, `precipitacion_mm` a granularidad diaria

**FUENTE 4 — Cuadrantes de Policía:**
- [x] `python src/pipeline.py --source f4` → `datos/raw/f4_cuadrantes.geojson`
- [x] `python src/transform.py --step f4` → `datos/procesados/features_cuadrantes_upz.csv` (111 UPZs)
- [x] Verificado: SÍ tiene `PCUNOMCAI` con nombre del CAI — NO se necesita cai_bogota.csv manual

### Semana 2 (2 junio – 6 junio) — EDA y construcción del dataset

**FUENTE 5 — NUSE 123:**
- [x] `python src/pipeline.py --source f5` → `datos/raw/f5_nuse_123.parquet` (128,314 filas, 2025–2026)
- [x] `python src/transform.py --step f5` → `datos/procesados/nuse_upz_mes.parquet` + `delitos_upz_mes.parquet` (**111,606 filas**, todos los 86 tipos NUSE × UPZ × mes, con flag `es_crimen`)
- [x] F5 NUSE es la **base del modelo** (F1 DAI es solo referencia EDA — no tiene desglose UPZ)
- [x] `ratio_nuse_delitos_upz` calculado automáticamente en el paso `silver`
- _Nota: Dataset NUSE solo disponible 2025–2026. Split temporal del modelo: TRAIN=Jan-Oct 2025, TEST=Nov 2025–2026._

**FUENTE 7 — Estratificación:**
- [x] `python src/pipeline.py --source f7` → `datos/raw/f7_estratificacion.parquet` (44,260 filas, CRS PCS_CarMAGBOG)
- [x] `python src/transform.py --step f7` → `datos/procesados/estrato_por_upz.csv` (43 UPZs cubiertas)
- [x] CRS PCS_CarMAGBOG resuelto con parámetros custom: lat_0=4.598055556, lon_0=-74.081361111

**FUENTE 8 — TransMilenio:**
- [x] `python src/pipeline.py --source f8` → `datos/raw/f8_transmilenio.geojson` (153 estaciones)
- [x] `python src/transform.py --step f8` → `datos/procesados/features_tm_upz.csv` (112 UPZs)
- [x] Verificado: `n_estaciones_tm` y `dist_tm_metros` presentes para todas las UPZs

**TABLA SILVER — unir todas las fuentes:**
- [x] `python src/transform.py --step silver` → `datos/procesados/silver_upz_mes.parquet` ✅
- [x] Tabla final: **111,606 filas × 20 columnas**, 120 UPZs, 86 tipos NUSE, 19 localidades, ene 2025–abr 2026

**Visualizaciones obligatorias del EDA:**
- [x] V1 — Mapa de calor de delitos NUSE por UPZ (Folium choropleta) → `graficas/v1_mapa_calor_upz.html`
- [x] V2 — Heatmap tipo de delito × mes (2025) → `graficas/v2_heatmap_tipo_mes.png`
- [x] V3 — Top 10 UPZs con más delitos → `graficas/v3_top10_upz_delitos.png`
- [x] V4 — Tendencia histórica 2018–2026 (DAI localidades + PN hurtos) → `graficas/v4_tendencia_anual.png`
- [x] V5 — Correlación lluvia vs. hurtos (scatter) → `graficas/v5_lluvia_vs_delitos.png`
- [x] V6 — Distribución de delitos por estrato promedio UPZ (boxplot) → `graficas/v6_estrato_vs_delitos.png`
- [x] V7 — Distribución n_delitos + cobertura policial (supplementary) → `graficas/v7_distribucion_cobertura.png`

**Entregables al cerrar Fase 1B:**
- [x] `datos/procesados/delitos_upz_mes.parquet` — todos los tipos NUSE × UPZ × mes + lags + flag `es_crimen` (**111,606 filas**)
- [x] `datos/procesados/clima_diario.parquet` — temperatura y precipitación diarios (2,338 días)
- [x] `datos/procesados/features_cuadrantes_upz.csv` — cuadrantes/km² + nombre CAI por UPZ (111 UPZs)
- [x] `datos/procesados/nuse_upz_mes.parquet` — incidentes NUSE agregados por UPZ × mes (todos los tipos)
- [x] `datos/procesados/estrato_por_upz.csv` — estrato promedio ponderado por UPZ (43 UPZs cubiertas)
- [x] `datos/procesados/features_tm_upz.csv` — n_estaciones_tm y dist_tm_metros por UPZ (112 UPZs)
- [x] `datos/procesados/silver_upz_mes.parquet` — **tabla unida final** (**20 columnas**, 111,606 filas, input para Gold)
- [x] `SeguroData_02_EDA.ipynb` — 6 visualizaciones requeridas + 1 complementaria, ejecutable de inicio a fin

---

## Fase 2 ⏳ — Modelo + Supabase + Nuevas Fuentes (7 – 20 junio 2026)

**Entregables:** `SeguroData_03_Features.ipynb` + `SeguroData_04_Modelo.ipynb`

### Setup Supabase + nuevas fuentes (7–10 junio) — EN PARALELO con modelo

- [ ] Crear proyecto Supabase → habilitar PostGIS + pgvector
- [ ] Ejecutar schema inicial (`scripts/setup_supabase.py`) + cargar Silver table
- [ ] Integrar F13 Cámaras Salvavidas SDM → spatial join → feature `n_camaras_upz`
- [ ] Integrar F14 Alumbrado UAESP → merge directo → feature `luminarias_led_upz`
- [ ] Integrar F11 IDU Obras Viales → spatial join → feature `km_via_intervenida_upz`
- [ ] Correr `ruptures` PELT sobre F1 DAI 2018–2026 por localidad → cargar en Supabase `change_points`

### Notebook 03 — Features (7–12 junio)

- [ ] Construir tabla maestra `datos/features/tabla_maestra_upz.parquet` con las **17 variables** (14 originales + F11/F13/F14)
- [ ] Definir `nivel_riesgo` (Y): `GROUP BY upz_cod, anio, mes` sobre `es_crimen=True` → top 25% = ALTO, 25–60% = MEDIO, resto = BAJO (1,920 filas modelo)
- [ ] Documentar tabla ontológica prescriptiva (17 filas SHAP→diagnóstico→entidad→acción) en celda 1
- [ ] Verificar imputación de estrato faltante (69 UPZs sin dato → mediana de la localidad)
- [ ] Normalizar features numéricas con StandardScaler → `datos/modelos/scaler.pkl`

### Notebook 04 — Modelo (13–20 junio)

- [ ] Split temporal: TRAIN = ene–oct 2025, TEST = nov 2025–abr 2026 (F5 NUSE solo disponible 2025–2026)
- [ ] Entrenar XGBoost con parámetros por defecto como baseline
- [ ] Métricas: Precision, Recall, F1 por clase (ALTO/MEDIO/BAJO) + AUC-ROC macro
- [ ] Tuning básico: RandomizedSearchCV sobre `max_depth`, `n_estimators`, `learning_rate`
- [ ] Calcular SHAP values → **pre-computar y guardar en Supabase** (NO on-demand)
- [ ] Análisis de sesgo: comparar F1 en UPZs estrato 1-2 vs. 5-6
- [ ] Guardar modelo: `datos/modelos/xgboost_segurodata.pkl`

### Track paralelo — Knowledge Graph F9/F10 (7–20 junio)

- [ ] Procesar F9 PDFs boletines SCJ → pdfplumber → texto limpio
- [ ] Procesar F10 RSS → feedparser → texto
- [ ] LangChain splitter → Claude embeddings → cargar en Supabase pgvector
- [ ] Verificar búsqueda semántica: query de prueba → resultados relevantes

---

## Fase 3 ⏳ — React + FastAPI + GraphRAG (21 junio – 10 julio 2026)

**Entregable:** `SeguroData_05_Dashboard.ipynb` + app React desplegada en Vercel

### Semana 1 — FastAPI backend + mapa base (21–27 junio)

- [ ] Skeleton FastAPI en `/backend` con endpoints `/predict`, `/explain`, `/query`
- [ ] Conectar XGBoost model + SHAP pre-computados desde Supabase
- [ ] Skeleton React + Vite + Tailwind + supabase-js
- [ ] deck.gl: PolygonLayer con 112 UPZs coloreadas (ALTO/MEDIO/BAJO) + hover tooltip
- [ ] Slider temporal funcional → cambia colores del mapa

### Semana 2 — Módulo Diagnóstico + Predicción (28 junio – 4 julio)

- [ ] Módulo 1: capas toggleables deck.gl (crimen · cámaras F13 · cuadrantes · alumbrado F14)
- [ ] Módulo 1: Heatmap día × hora (Plotly React) + tendencia con change points marcados
- [ ] Módulo 2: click en UPZ → FastAPI /predict → panel con nivel_riesgo + probabilidades
- [ ] Módulo 2: mapa predictivo rojo/amarillo/verde + top-10 UPZs en riesgo ALTO

### Semana 3 — Módulo Prescriptivo + Chatbot (5–10 julio)

- [ ] Módulo 3: tabla ontológica + SHAP top feature → diagnóstico → Claude API → recomendación operacional
- [ ] Módulo 3: panel CAI (nombre + dirección + turno) + indicador change point (estructural vs temporal)
- [ ] Módulo 4: chat input → FastAPI /query → LangChain SupabaseVectorStore → Claude API → respuesta con citas
- [ ] Probar 10 preguntas tipo de los 3 perfiles de usuario

### Deploy

- [ ] FastAPI → Cloud Run: `gcloud run deploy segurodata-api --source ./backend --allow-unauthenticated`
- [ ] Configurar variables en Cloud Run: OPENROUTER_API_KEY, LLM_MODEL, SUPABASE_URL, SUPABASE_SERVICE_KEY
- [ ] React → Vercel: conectar repo GitHub → `/frontend`
- [ ] Configurar variables en Vercel: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL (URL de Cloud Run)
- [ ] Verificar URL pública funciona desde móvil
- [ ] Pre-demo: visitar URL de Cloud Run 2 minutos antes de la presentación para calentar el contenedor

---

## Fase 4 ⏳ — Documentación, Video y Entrega (11 julio – 1 agosto 2026)

**Entregable:** `SeguroData_06_Deployment.ipynb` + README + Video + Registro

> ⚠️ Verificar fecha exacta de entrega/registro en datos.gov.co. Final confirmado: GovCamps primera semana de agosto 2026.

- [ ] `README.md`: descripción, URL Railway + Vercel + Supabase, instrucciones instalación completas
- [ ] Notebook 06: URLs de producción, schema Supabase, instrucciones reproducción local, decisiones de diseño
- [ ] Video pitch de 3 minutos: problema → solución → demo (mapa + prescriptivo + chatbot)
- [ ] Auditoría de git history para API keys antes de hacer repo público
- [ ] Repositorio GitHub en modo público
- [ ] Registrar en datos.gov.co → sección "Usos" con enlace al repo — **OBLIGATORIO**

---

## Riesgos y planes de contingencia

| Riesgo | Probabilidad | Plan B |
|--------|-------------|--------|
| GeoJSON Delito Alto Impacto no tiene columna `hora` | Media | Imputar franja horaria desde `fecha` si la hora está en el timestamp |
| Cuadrantes dataset sin info de CAI | Media | Crear `cai_bogota.csv` manual (~80 filas) — ver Fase 1 Semana 1 |
| Memoria insuficiente en Colab para Estratificación (FUENTE 7) | Alta | Pre-calcular en Colab Pro o descargar a Drive → cargar desde Drive |
| Streamlit Cloud tarda en desplegar | Alta | Iniciar deploy al principio de Fase 3, no al final |
| Claude API Key cuota agotada | Baja | Cachear respuestas generadas; limitar chatbot a 20 consultas/sesión |
| Fecha real del concurso es agosto (GovCamps) | Media | Si se confirma, extender Fase 3 para refinar el dashboard |
