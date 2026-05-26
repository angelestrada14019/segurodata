# CRONOGRAMA.md — Fases del Proyecto SeguroData Bogotá

> Entrega: **13 julio 2026** (GitHub público + registro datos.gov.co) · Sustentación: 14–17 julio
>
> **Nota sobre fecha:** Existe posibilidad de que el evento final sea GovCamps agosto 2026. Si se confirma, hay ~3 semanas extra. Verificar en datos.gov.co antes de la Fase 4.

---

## Vista general

```
MAYO           JUNIO                          JULIO
Fase 0 ✅ | Fase 1 ▶ | Fase 2 ⏳ | Fase 3 ⏳ | Fase 4 ⏳
25 May    |  26M–6J  |  7–20 Jun | 21J–10Jul | 11–13 Jul
[Plan]    | [EDA]    | [Modelo]  | [Dashboard+IA] | [Docs+Entrega]
```

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

## Fase 1 ▶ — EDA (26 mayo – 6 junio 2026)

**Entregable:** `SeguroData_02_EDA.ipynb` — análisis exploratorio completo

### Semana 1 (26 mayo – 1 junio) — Descarga y limpieza

**FUENTE 1 — Delito de Alto Impacto (ZIP GeoJSON):**
- [ ] Descargar `dai_geojson.zip` → `datos/raw/`
- [ ] Cargar con GeoPandas, verificar columnas (`tipologia_delito`, `lat`, `lon`, `fecha`, `hora`, `UPZ`)
- [ ] Filtrar solo registros con coordenadas válidas dentro de Bogotá (lat: 3.7–4.9, lon: -74.4–-73.9)
- [ ] Agregar por UPZ + mes: tabla de conteos históricos 2020–2024

**FUENTE 2 — UPZ Shapefile:**
- [ ] Cargar desde URL directa con `gpd.read_file(URL_UPZ)`
- [ ] Verificar N=112 polígonos, CRS EPSG:4326
- [ ] Explorar columnas disponibles (código UPZ, nombre, localidad, área)

**FUENTE 3 — Open-Meteo:**
- [ ] Descargar clima horario 2020–2024 con `src/etl.open_meteo()`
- [ ] Guardar como `datos/raw/clima_bogota_2020_2024.parquet`
- [ ] Agregar a granularidad diaria (temperatura y precipitación promedio)

**FUENTE 4 — Cuadrantes de Policía:**
- [ ] Descargar GeoJSON de cuadrantes → `datos/raw/cuadrantes_policia.geojson`
- [ ] Verificar columnas: confirmar si tiene `nombre_cai` con info de contacto
- [ ] Si NO tiene → crear `datos/raw/cai_bogota.csv` con nombre, dirección y cuadrante (~80 CAIs)

### Semana 2 (2 junio – 6 junio) — EDA y construcción del dataset

**FUENTE 5 — NUSE 123:**
- [ ] Descargar via CKAN API (`src/etl.ckan_query_all`) con paginación
- [ ] Calcular `ratio_nuse_delitos_upz` = CANT_INCIDENTES_NUSE / n_delitos_DAI por UPZ·mes

**FUENTE 7 — Estratificación:**
- [ ] Cargar desde URL directa (100K+ manzanas — advertencia memoria Colab)
- [ ] Calcular `estrato_promedio_upz` por spatial join manzana centroide → UPZ
- [ ] Guardar resultado como `datos/procesados/estrato_por_upz.csv` para no recalcular

**FUENTE 8 — TransMilenio:**
- [ ] Descargar GeoJSON estaciones → `datos/raw/estaciones_transmilenio.geojson`
- [ ] Calcular `n_estaciones_tm_upz` y `dist_tm_metros` por spatial join

**Visualizaciones obligatorias del EDA:**
- [ ] Mapa de calor de hurtos por UPZ (Folium choropleta)
- [ ] Heatmap día de semana × hora del día
- [ ] Top 10 UPZs con más delitos por año 2020–2024
- [ ] Tendencia anual 2020–2024 (total ciudad + las 5 UPZs más críticas)
- [ ] Correlación lluvia vs. número de hurtos (scatter plot)
- [ ] Distribución de estrato promedio por UPZ (boxplot)

**Entregable al cerrar Fase 1:**
- `datos/procesados/delitos_por_upz_mes.parquet` — tabla maestra de delitos agregados
- `datos/procesados/estrato_por_upz.csv` — pre-calculado, no recalcular
- `datos/procesados/features_espaciales_upz.csv` — cuadrantes/km², estaciones TM, distancia TM

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
