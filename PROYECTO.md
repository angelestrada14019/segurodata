# PROYECTO.md — SeguroData Bogotá

> Documento activo de gobernanza. Referencia rápida del alcance acordado. Actualizar cuando cambie algo sustancial.

---

## Identidad

| Campo | Valor |
|-------|-------|
| **Nombre** | SeguroData Bogotá |
| **Concurso** | Datos al Ecosistema 2026 — MinTIC |
| **Reto** | #2 — Seguridad Ciudadana y Justicia |
| **Nivel** | **Medio** |
| **Ciudad piloto** | Bogotá D.C. |
| **Unidad de análisis** | UPZ (112 zonas) |
| **Entrega** | 13 julio 2026 (GitHub + registro datos.gov.co) |
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

## Las 8 fuentes activas

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

---

## Stack y arquitectura de datos

```
datos/raw/        ← Bronze: archivos originales (ZIP, GeoJSON, CSV, Parquet)
datos/procesados/ ← Silver: datos limpios, agregados por UPZ
datos/features/   ← Gold: tabla_maestra_upz.parquet con las 14 variables
datos/modelos/    ← Model: xgboost_segurodata.pkl + scaler.pkl + shap_values.pkl
graficas/         ← Outputs EDA (PNG, HTML)
```

**Stack Python:** `pandas · geopandas · shapely · requests · xgboost · scikit-learn · shap · anthropic · streamlit · plotly · folium`

**No hay:** FastAPI, Docker, Raspberry Pi, LangChain, Hawkes Process.

---

## Estado actual por fase

| Fase | Fechas | Entregable | Estado |
|------|--------|-----------|--------|
| Fase 0 | hasta 25 may | Notebook 01 — Plan + catálogo | ✅ Completo |
| Fase 1 | 26 may – 6 jun | Notebook 02 — EDA de 8 fuentes | ▶ En curso |
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
| ETL scripts | `src/etl.py` | Conectores CKAN, Socrata, ArcGIS, Open-Meteo |
| Validación de fuentes | `src/validar_fuentes.py` | Genera el Excel de 20 fuentes |
