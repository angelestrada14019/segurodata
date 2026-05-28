# PROYECTO.md — SeguroData Bogotá

> Documento activo de gobernanza. Referencia rápida del alcance acordado. Actualizar cuando cambie algo sustancial.

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | SeguroData Bogotá |
| **Repositorio** | https://github.com/angelestrada14019/segurodata |
| **Concurso** | Datos al Ecosistema 2026 — MinTIC |
| **Reto** | #2 — Seguridad Ciudadana y Justicia |
| **Nivel** | **Medio** |
| **Ciudad piloto** | Bogotá D.C. |
| **Unidad de análisis** | UPZ (112 zonas) |
| **Entrega** | 13 julio 2026 (GitHub público + registro datos.gov.co) |
| **Puntaje estimado** | 87 / 100 |

---

## Los 4 módulos

| # | Módulo | Tipo | Usuario principal | Tecnología |
|---|--------|------|-----------------|-----------|
| 1 | Diagnóstico | Descriptivo | Sec. Seguridad, ciudadano | GeoPandas + Folium + Plotly |
| 2 | Predicción | ML | Comandante de CAI | XGBoost + SHAP |
| 3 | Recomendación | IA Generativa | Comandante de CAI | Claude API |
| 4 | Chatbot | NLP | Ciudadano, funcionario | Claude API |

Un solo dashboard Streamlit, cuatro pestañas.

---

## Las 10 fuentes activas (+ F11/F12 planificadas)

| # | Nombre | Plataforma | Resource ID / URL clave | Rol |
|---|--------|-----------|------------------------|-----|
| F1 | Delito de Alto Impacto | CKAN — ZIP | `7b270013-42ca-436b-9c1e-3bcb7d280c6b` | **Variable objetivo Y** |
| F2 | UPZ Shapefile — IDECA | CKAN — URL directa | `a5c8c591-0708-420f-8eb7-9f3147e21c40` | Base espacial |
| F3 | Open-Meteo Clima | REST API | `archive-api.open-meteo.com` | Clima en tiempo real |
| F4 | Cuadrantes Policía | CKAN — ZIP | `f0ad2ee3-bfd0-4825-9b31-bff9041649fa` | Cobertura policial + CAI |
| F5 | NUSE 123 — C4 | CKAN Datastore | `30d65a8b-d0ed-4e95-977e-0d7cc2ea89ef` | Proxy subregistro |
| F6 | Hurto Personas — PN | Socrata | `4rxi-8m8d` | Benchmarking nacional |
| F7 | Estratificación SDP | CKAN — URL directa | `29f2d770-bd5d-4450-9e95-8737167ba12f` | Socioeconómica + equidad |
| F8 | Estaciones TransMilenio | CKAN | `9be8b6fb-8059-492f-a866-4a1ac031c502` | Movilidad / afluencia |
| F9 | Boletines SCJ — Sec. Distrital Seguridad | scj.gov.co | N/A (texto) | Corpus LLM — GraphRAG |
| F10 | Noticias RSS — El Tiempo / Espectador | RSS público | N/A (texto) | Corpus LLM — GraphRAG |

> F9 y F10 no entran en XGBoost — son corpus de texto para el GraphRAG y Claude API (Módulos 3 y 4). F11 (IDU obras) y F12 (Plan Desarrollo) se planifican para Fase 2 y Fase 3 respectivamente.

**Fuente adicional opcional:** Medicina Legal Lesiones (Socrata `79dd-d24f`) — refuerza análisis de subregistro en la sustentación oral.

---

## Las 14 variables del modelo

| Grupo | Variables |
|-------|----------|
| Históricas (lag) | `n_delitos_upz_4sem`, `n_delitos_upz_8sem`, `tipo_delito_dominante` |
| Temporales | `dia_semana`, `franja_horaria`, `mes`, `es_fin_semana` |
| Climáticas | `temperatura_c`, `precipitacion_mm` |
| Espaciales | `estrato_promedio_upz`, `cuadrantes_por_km2`, `n_estaciones_tm`, `dist_tm_metros` |
| Subregistro | `ratio_nuse_delitos_upz` |
| **Objetivo (Y)** | `nivel_riesgo` — ALTO / MEDIO / BAJO |

> La selección final de variables (correlación, VIF, importancia SHAP) ocurre en la capa Gold — Notebook 03.

---

## Stack y arquitectura de datos

```
datos/raw/        ← Bronze: archivos originales (ZIP, GeoJSON, Parquet)  — src/pipeline.py
datos/procesados/ ← Silver: datos limpios, agregados por UPZ             — src/transform.py
datos/features/   ← Gold: tabla_maestra_upz.parquet con las 14 variables — Notebook 03
datos/modelos/    ← Model: xgboost_segurodata.pkl + scaler.pkl + shap_values.pkl
graficas/         ← Outputs EDA (PNG, HTML)
```

**Stack Python:** `polars · geopandas · shapely · requests · xgboost · scikit-learn · shap · anthropic · streamlit · plotly · folium`

**No hay:** FastAPI, Docker, Raspberry Pi, LangChain, OpenAI, Hawkes Process.

---

## Estructura de ramas (GitHub)

| Rama | Capa | Estado |
|------|------|--------|
| `main` | Integración — siempre estable | ✅ Activa |
| `bronze` | Extracción Bronze | ✅ Completo |
| `silver` | Transformación Silver | ✅ Completo |
| `gold` | Feature engineering | ⏳ Pendiente |
| `model` | XGBoost + SHAP | ⏳ Pendiente |
| `dashboard` | Streamlit + Claude API | ⏳ Pendiente |

---

## Estado actual por fase

| Fase | Fechas | Entregable | Estado |
|------|--------|-----------|--------|
| Fase 0 | hasta 25 may | Notebook 01 — Plan + catálogo | ✅ Completo |
| Fase 1A | 26 may – 27 may | Bronze layer — src/pipeline.py | ✅ Completo |
| Fase 1B | 27 may – 6 jun | Silver layer — src/transform.py | ✅ Completo |
| Fase 1C | hasta 6 jun | Notebook 02 — EDA de 10 fuentes | ✅ Completo |
| Fase 2 | 7 – 20 jun | Notebooks 03+04 — XGBoost + SHAP | ⏳ Pendiente |
| Fase 3 | 21 jun – 10 jul | Notebook 05 — Dashboard + Claude API | ⏳ Pendiente |
| Fase 4 | 11 – 13 jul | Notebook 06 — Docs + video + registro | ⏳ Pendiente |

---

## El argumento diferenciador

> *"SeguroData no solo predice dónde habrá delitos — le dice exactamente a qué cuadrante de la Policía tiene que ir y por qué. Ese es el puente que hoy no existe entre los datos abiertos de Bogotá y la acción institucional."*

La conexión CAI (Módulo 3) diferencia al proyecto de cualquier análisis descriptivo o predictivo sin capa de recomendación operativa. Ningún equipo que solo use descriptivo/predictivo tendrá esta capa.

---

## Documentación de referencia

| Documento | Ubicación | Para qué |
|-----------|----------|---------|
| Catálogo 20 fuentes (investigación) | `docs/INVESTIGACION_FUENTES.md` | Referencia fuentes descartadas y alternativas |
| Excel de fuentes validadas (4 hojas) | `docs/fuentes_validadas.xlsx` | Metadatos, URLs, estado de cada fuente |
| Estado del arte internacional | `docs/ESTADO_DEL_ARTE.md` | 20+ sistemas, 18 papers, lecciones aprendidas |
| Guía capa Silver | `docs/TRANSFORMACION.md` | Instrucciones completas para el equipo de transformación |
| Conectores ETL | `src/etl.py` | CKAN, Socrata, ArcGIS, Open-Meteo de bajo nivel |
| Pipeline Bronze | `src/pipeline.py` | Extracción incremental de las 10 fuentes |
| Pipeline Silver | `src/transform.py` | Limpieza, joins espaciales, tabla silver |
| Validación de fuentes | `src/validar_fuentes.py` | Genera el Excel de 20 fuentes |
| Provenance fuentes | `docs/FUENTES_PROVENANCE.md` | URLs, licencias, causalidad — para el jurado |
