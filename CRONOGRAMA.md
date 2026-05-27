# CRONOGRAMA.md — Fases del Proyecto SeguroData Bogotá

> Entrega: **13 julio 2026** (GitHub público + registro datos.gov.co) · Sustentación: 14–17 julio
>
> **Nota sobre fecha:** Existe posibilidad de que el evento final sea GovCamps agosto 2026. Si se confirma, hay ~3 semanas extra. Verificar en datos.gov.co antes de la Fase 4.

---

## Vista general

```
MAYO                        JUNIO                          JULIO
Fase 0 ✅ | Fase 1A ✅ | Fase 1B 🔄 | Fase 2 ⏳ | Fase 3 ⏳ | Fase 4 ⏳
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
- ✅ Catálogo de 8 fuentes con URLs verificadas, variables y código de carga
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
- ✅ `src/pipeline.py` — 8 extractores con lógica incremental (Last-Modified / append / dedup)
- ✅ `PipelineState` — estado persistente en `.pipeline_state.json`
- ✅ CLI: `--dry-run`, `--status`, `--source`, `--force`, `--verbose`
- ✅ GitHub: rama `bronze` publicada + `main` con commit inicial
- ✅ Probado: F3 descargó 56,064 filas · segunda ejecución → skip instantáneo
- ✅ GitHub Action `etl-semanal.yml` creado (desactivado hasta Fase 3)

---

## Fase 1B 🔄 — Silver layer + EDA (27 mayo – 6 junio 2026)

**Entregables:**
- `src/transform.py` — pipeline Silver (rama `silver`) 🔄
- `SeguroData_02_EDA.ipynb` — análisis exploratorio completo ⏳

### Semana 1 (26 mayo – 1 junio) — Descarga y limpieza

> ✅ La descarga ya está automatizada — usar `python src/pipeline.py` en lugar de los pasos manuales de abajo.

**FUENTE 1 — Delito de Alto Impacto (ZIP GeoJSON):**
- [x] `python src/pipeline.py --source f1` → `datos/raw/f1_delito_alto_impacto.parquet`
- [ ] Verificar columnas en EDA (`tipologia_delito`, `lat`, `lon`, `fecha`, `hora`, `UPZ`)
- [ ] `python src/transform.py --step f1` → `datos/procesados/delitos_upz_mes.parquet`

**FUENTE 2 — UPZ Shapefile:**
- [x] `python src/pipeline.py --source f2` → `datos/raw/f2_upz.geojson`
- [ ] Verificar N=112 polígonos, CRS EPSG:4326
- [ ] Explorar columnas disponibles (código UPZ, nombre, localidad, área)
- _Nota: F2 no tiene paso transform propio — es referencia espacial usada en los spatial joins de F4, F7 y F8._

**FUENTE 3 — Open-Meteo:**
- [x] `python src/pipeline.py --source f3` → `datos/raw/f3_clima_bogota.parquet` (descarga incremental desde `max(fecha)`)
- [ ] `python src/transform.py --step f3` → `datos/procesados/clima_diario.parquet`
- [ ] Verificar columnas: `temperatura_promedio_c`, `precipitacion_mm` agregadas a granularidad diaria

**FUENTE 4 — Cuadrantes de Policía:**
- [x] `python src/pipeline.py --source f4` → `datos/raw/f4_cuadrantes.geojson`
- [ ] `python src/transform.py --step f4` → `datos/procesados/features_cuadrantes_upz.csv`
- [ ] Verificar columnas: confirmar si tiene `nombre_cai` con info de contacto
- [ ] Si NO tiene `nombre_cai` → crear `datos/raw/cai_bogota.csv` manual (~80 CAIs: nombre, dirección, cuadrante)

### Semana 2 (2 junio – 6 junio) — EDA y construcción del dataset

**FUENTE 5 — NUSE 123:**
- [x] `python src/pipeline.py --source f5` → `datos/raw/f5_nuse_123.parquet` (descarga por año + dedup)
- [ ] `python src/transform.py --step f5` → `datos/procesados/nuse_upz_mes.parquet`
- [ ] `ratio_nuse_delitos_upz` se calcula automáticamente en el paso `silver` (NUSE / delitos por UPZ·mes)

**FUENTE 7 — Estratificación:**
- [x] `python src/pipeline.py --source f7` → `datos/raw/f7_estratificacion.parquet`
- [ ] `python src/transform.py --step f7 --force` → `datos/procesados/estrato_por_upz.csv` ⚠️ pesado (~115K polígonos, spatial join por centroides)
- [ ] Si la RAM se agota en Colab gratuito: ver `docs/TRANSFORMACION.md` (alternativas con Colab Pro o Drive)

**FUENTE 8 — TransMilenio:**
- [x] `python src/pipeline.py --source f8` → `datos/raw/f8_transmilenio.geojson`
- [ ] `python src/transform.py --step f8` → `datos/procesados/features_tm_upz.csv`
- [ ] Verificar `n_estaciones_tm` y `dist_tm_metros` por UPZ

**TABLA SILVER — unir todas las fuentes:**
- [ ] `python src/transform.py --step silver` → `datos/procesados/silver_upz_mes.parquet` (18 columnas, ~5–8K filas)
- [ ] O correr todo de un tirón: `python src/transform.py` → ejecuta f1 · f3 · f4 · f5 · f7 · f8 · silver en orden

**Visualizaciones obligatorias del EDA:**
- [ ] Mapa de calor de hurtos por UPZ (Folium choropleta)
- [ ] Heatmap día de semana × hora del día
- [ ] Top 10 UPZs con más delitos por año 2020–2024
- [ ] Tendencia anual 2020–2024 (total ciudad + las 5 UPZs más críticas)
- [ ] Correlación lluvia vs. número de hurtos (scatter plot)
- [ ] Distribución de estrato promedio por UPZ (boxplot)

**Entregables al cerrar Fase 1B:**
- `datos/procesados/delitos_upz_mes.parquet` — delitos por UPZ × mes + lags 4sem / 8sem + tipo dominante
- `datos/procesados/clima_diario.parquet` — temperatura y precipitación diarios (2020–hoy)
- `datos/procesados/features_cuadrantes_upz.csv` — densidad de cuadrantes por km² por UPZ
- `datos/procesados/nuse_upz_mes.parquet` — incidentes NUSE 123 por UPZ × mes
- `datos/procesados/estrato_por_upz.csv` — estrato promedio ponderado por UPZ (pre-calculado, ⚠️ no recalcular)
- `datos/procesados/features_tm_upz.csv` — n_estaciones_tm y dist_tm_metros por UPZ
- `datos/procesados/silver_upz_mes.parquet` — **tabla unida final** (18 columnas, input para Gold)

---

## Fase 2 ⏳ — Modelo XGBoost + SHAP (7 – 20 junio 2026)

**Entregables:** `SeguroData_03_Features.ipynb` + `SeguroData_04_Modelo.ipynb`

### Notebook 03 — Features (7–12 junio)

- [ ] Construir tabla maestra `datos/features/tabla_maestra_upz.parquet` con las 14 variables
- [ ] Definir `nivel_riesgo` (Y): top 25% UPZs por mes = ALTO, 25–60% = MEDIO, rest = BAJO
- [ ] Verificar balanceo de clases (crimen es raro → esperar desbalance)
- [ ] Normalizar features numéricas con StandardScaler (guardado en `datos/modelos/scaler.pkl`)

### Notebook 04 — Modelo (13–20 junio)

- [ ] Split temporal: TRAIN = 2020–2023, TEST = 2024 (NO split aleatorio)
- [ ] Entrenar XGBoost con parámetros por defecto como baseline
- [ ] Métricas: Precision, Recall, F1 por clase (ALTO/MEDIO/BAJO) + AUC-ROC macro
- [ ] Tuning básico: GridSearch sobre `max_depth`, `n_estimators`, `learning_rate`
- [ ] Calcular SHAP values → Feature Importance por UPZ
- [ ] Análisis de sesgo: comparar F1 en UPZs estrato 1-2 vs. 5-6 (¿el modelo discrimina?)
- [ ] Guardar modelo: `datos/modelos/xgboost_segurodata.pkl`

---

## Fase 3 ⏳ — Dashboard + IA Generativa (21 junio – 10 julio 2026)

**Entregable:** `SeguroData_05_Dashboard.ipynb` + app Streamlit desplegada

### Módulo 1 — Diagnóstico (semana del 21 junio)

- [ ] Mapa interactivo Folium con choropleta de hurtos por UPZ + filtros (año, tipo delito)
- [ ] Top 5 localidades con más delitos — gráfica de barras
- [ ] Heatmap día × hora en Streamlit (Plotly)
- [ ] Tendencia anual con variación %

### Módulo 2 — Predicción (semana del 28 junio)

- [ ] Cargar modelo XGBoost en la app Streamlit (joblib.load)
- [ ] Input: seleccionar UPZ + fecha + hora → output: ALTO/MEDIO/BAJO + probabilidades
- [ ] Mapa predictivo de Bogotá: todas las UPZs coloreadas rojo/amarillo/verde
- [ ] Tabla de top-10 UPZs en riesgo ALTO para la fecha seleccionada

### Módulos 3 y 4 — Recomendación + Chatbot (semana del 5 julio)

- [ ] Configurar `CLAUDE_API_KEY` como secreto en Streamlit Cloud
- [ ] Módulo 3: prompt que convierte SHAP values → mensaje de recomendación para el comandante
- [ ] Incluir nombre y dirección del CAI correspondiente al cuadrante de mayor riesgo
- [ ] Módulo 4: chatbot que responde preguntas con contexto de la tabla maestra UPZ
- [ ] Probar con 10 preguntas tipo de los 3 usuarios (comandante, funcionario, ciudadano)

### Deploy

- [ ] Desplegar en Streamlit Cloud (conectar repo GitHub → Streamlit Cloud → branch main)
- [ ] Verificar que el secreto CLAUDE_API_KEY está configurado en Streamlit Cloud
- [ ] Verificar URL pública funciona desde el móvil (demo para la sustentación)

---

## Fase 4 ⏳ — Documentación, Video y Entrega (11 – 13 julio 2026)

**Entregable:** `SeguroData_06_Deployment.ipynb` + README + Video + Registro

- [ ] `README.md` completo: descripción, URL del dashboard, instrucciones `pip install -r requirements.txt`
- [ ] Notebook 06: URLs de producción, instrucciones de reproducción local, decisiones de diseño
- [ ] Video pitch de 3 minutos: problema → solución → demo del dashboard
- [ ] **13 julio:** Repositorio GitHub en modo público
- [ ] **13 julio:** Registrar en datos.gov.co → sección "Usos" con enlace al repo — **OBLIGATORIO**

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
