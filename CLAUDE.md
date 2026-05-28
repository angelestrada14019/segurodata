# CLAUDE.md — Contexto del Proyecto para Claude

> Lee este archivo al inicio de cada sesión. Contiene todo lo que necesitas saber para asistir de forma efectiva.

---

## Qué es este proyecto

**SeguroData Bogotá** — sistema de predicción y prescripción de crimen con IA para Bogotá D.C., desarrollado para el concurso **"Datos al Ecosistema 2026"** convocado por MinTIC.

- **Nivel del concurso:** Medio — Reto #2 Seguridad Ciudadana y Justicia
- **Entrega:** 13 de julio de 2026 (código en GitHub + registro en datos.gov.co)
- **Sustentación oral:** 14–17 julio 2026 (10 minutos + preguntas)
- **Unidad de análisis:** UPZ — 112 zonas de Bogotá

El sistema responde tres preguntas concretas:

| Pregunta | Módulo | Tecnología |
|----------|--------|-----------|
| ¿Qué está pasando? | 1 — Diagnóstico | GeoPandas + Folium + Plotly |
| ¿Qué va a pasar? | 2 — Predicción | XGBoost + SHAP |
| ¿Qué hacer? | 3 — Recomendación | Claude API (Anthropic) |
| Consulta en lenguaje natural | 4 — Chatbot | Claude API + contexto de datos |

---

## Stack técnico

| Capa | Tecnologías |
|------|------------|
| Ingesta y limpieza | `pandas`, `geopandas`, `requests` |
| Análisis espacial | `geopandas`, `shapely`, `folium` |
| Modelo ML | `xgboost`, `scikit-learn`, `shap` |
| IA Generativa | **Claude API** (`anthropic` SDK) |
| Dashboard | `streamlit`, `plotly`, `folium` |
| Repositorio | GitHub (público, obligatorio para el concurso) |

**No hay FastAPI, Docker, LangChain, OpenAI, Raspberry Pi, ni proceso de Hawkes en este proyecto.** El dashboard Streamlit es autónomo (carga el modelo directamente, sin API backend separada).

---

## Las 10 fuentes de datos activas (+ F11/F12 planificadas)

| # | Fuente | Plataforma | Rol en el modelo |
|---|--------|-----------|-----------------|
| F1 | Delito de Alto Impacto — Sec. Seguridad | CKAN — descarga ZIP | EDA histórico 2018–2026 (granularidad localidad, no UPZ) |
| F2 | UPZ Shapefile — IDECA | ArcGIS REST | Base espacial — spatial joins |
| F3 | Open-Meteo — Clima Bogotá | REST API (sin clave) | Features climáticas en tiempo real |
| F4 | Cuadrantes de Policía — MEBOG | CKAN — descarga ZIP | Feature cobertura policial + conexión CAI |
| F5 | Incidentes NUSE 123 — C4 | CKAN Datastore API | **BASE Silver**: genera 111,606 filas × 20 cols |
| F6 | Hurto Personas — Policía Nacional | Socrata `4rxi-8m8d` | Benchmarking nacional — contexto oral |
| F7 | Estratificación por manzana — SDP | CKAN — URL directa | Feature socioeconómica + análisis sesgo |
| F8 | Estaciones TransMilenio — TM S.A. | ArcGIS REST | Features movilidad/afluencia |
| F9 | Boletines SCJ — Sec. Distrital Seguridad | scj.gov.co (PDFs) | Corpus LLM → GraphRAG (NO entra en XGBoost) |
| F10 | Noticias RSS — El Tiempo / Espectador | RSS público | Corpus LLM → GraphRAG (NO entra en XGBoost) |

> **F11 (IDU obras)** y **F12 (Plan Desarrollo Bogotá 2024-2027)** se planifican para Fase 2 y Fase 3.  
> **Silver**: 111,606 filas × 20 cols — generadas por F5 NUSE. F1/F6 no tienen desglose UPZ.

**Investigación completa de 20 fuentes** (incluyendo descartadas y alternativas) en el [Wiki — Investigacion-Fuentes](https://github.com/angelestrada14019/segurodata/wiki/Investigacion-Fuentes) y `docs/fuentes_validadas.xlsx`.

---

## Las 14 variables del modelo XGBoost

```
HISTÓRICAS (lag):
  n_delitos_upz_4sem      ← conteo delitos últimas 4 semanas por UPZ
  n_delitos_upz_8sem      ← conteo delitos últimas 8 semanas por UPZ
  tipo_delito_dominante   ← categoría de delito más frecuente en la UPZ

TEMPORALES:
  dia_semana              ← lunes=0 … domingo=6
  franja_horaria          ← madrugada / mañana / tarde / noche
  mes                     ← 1-12
  es_fin_semana           ← binaria

CLIMÁTICAS (Open-Meteo):
  temperatura_c           ← temperatura °C hora del evento
  precipitacion_mm        ← precipitación mm hora del evento

ESPACIALES:
  estrato_promedio_upz    ← promedio ponderado del estrato por manzana
  cuadrantes_por_km2      ← densidad de cuadrantes policiales en la UPZ
  n_estaciones_tm         ← número de estaciones TM dentro de la UPZ
  dist_tm_metros          ← distancia al centroide de la UPZ a TM más cercana

SUBREGISTRO:
  ratio_nuse_delitos_upz  ← llamadas al 123 / delitos formales por UPZ·mes

VARIABLE OBJETIVO (Y):
  nivel_riesgo: ALTO / MEDIO / BAJO  (umbralizado por percentiles del dataset)
```

---

## Estructura de carpetas

```
proyecto/
├── datos/
│   ├── raw/              ← Bronze: archivos como se descargan (generados por pipeline.py)
│   │   └── boletines_scj/← F9: PDFs descargados de SCJ
│   ├── procesados/       ← Silver: datos limpios y unificados (generados por transform.py)
│   ├── features/         ← Gold: tabla maestra UPZ con las 14 variables (Notebook 03)
│   ├── grafo/            ← GraphRAG: índice nano-graphrag persistido (Fase 3)
│   └── modelos/          ← Model: XGBoost entrenado + SHAP values (Notebook 04)
├── graficas/             ← Outputs visuales del EDA (7 gráficas V1-V7)
├── src/
│   ├── etl.py            ← 4 conectores de bajo nivel: CKAN, Socrata, ArcGIS, Open-Meteo
│   ├── pipeline.py       ← Extracción incremental Bronze (10 fuentes F1-F10)
│   ├── transform.py      ← Transformación Silver (limpieza + spatial joins)
│   └── validar_fuentes.py← genera fuentes_validadas.xlsx con 20 fuentes
├── docs/
│   ├── diagrama_arquitectura.svg  ← diagrama visual de la arquitectura (linkeado en README)
│   └── fuentes_validadas.xlsx     ← Excel validado (4 hojas)
├── wiki_pages/           ← FUENTE ÚNICA de documentación pública → PUSH_WIKI.bat → GitHub wiki
│   ├── Home.md / Fuentes-de-Datos.md / Arquitectura.md / Modulos.md
│   ├── Metodologia.md / Replicacion.md / Instalacion.md
│   ├── Transformacion.md / Estado-del-Arte.md / Provenance.md
│   ├── Investigacion-Fuentes.md / Reglas-Concurso.md
│   └── PUSH_WIKI.bat     ← helper: git push al wiki (wiki ya inicializado en GitHub)
├── .github/
│   └── workflows/
│       └── etl-semanal.yml ← GitHub Action ETL semanal (desactivado)
├── .claude/commands/     ← slash commands del proyecto
├── CLAUDE.md             ← este archivo (contexto IA)
├── CRONOGRAMA.md         ← checklists de tareas por fase ✅/⏳
├── requirements.txt
├── README.md
├── SeguroData_01_Plan_y_Fuentes.ipynb  ← Notebook 01 ✅
└── SeguroData_02_EDA.ipynb             ← Notebook 02 ✅
```

Los notebooks del proyecto siguen el esquema `SeguroData_0X_Nombre.ipynb`:
- `SeguroData_01_Plan_y_Fuentes.ipynb` — Plan + catálogo ✅
- `SeguroData_02_EDA.ipynb` — Diagnóstico descriptivo (Módulo 1)
- `SeguroData_03_Features.ipynb` — Construcción de las 14 variables
- `SeguroData_04_Modelo.ipynb` — XGBoost + backtesting + SHAP (Módulos 2-3)
- `SeguroData_05_Dashboard.ipynb` — Streamlit + Claude API (Módulos 3-4)
- `SeguroData_06_Deployment.ipynb` — Deploy en Streamlit Cloud + registro

---

## El diferenciador clave

Todos los equipos predirán crimen. Lo que distingue a SeguroData:

> *"No solo predice dónde habrá delitos — le dice exactamente a qué cuadrante de la Policía tiene que ir y por qué. Ese es el puente que hoy no existe entre los datos abiertos de Bogotá y la acción institucional."*

El Módulo 3 usa SHAP para identificar la causa dominante del riesgo y conecta directamente con el CAI responsable — sin esto, la predicción es descriptiva, no operativa.

---

## Cómo ayudar en este proyecto

**Cuando el usuario traiga código:** revisar con énfasis en correctitud, reproducibilidad en Colab, y eficiencia con datasets grandes. Los dos datasets más pesados: F6 Hurto PN (638K filas, solo benchmarking) y F7 Estratificación (44K polígonos de manzanas — el spatial join agota RAM en Colab gratuito).

**Cuando pida análisis:** usar el contexto de Bogotá — 112 UPZs, localidades, las 10 fuentes activas (F1-F10). No generalizar.

**Cuando pida texto para el chatbot o recomendaciones:** el Módulo 3 y 4 usan Claude API. Los mensajes son operacionales (lenguaje del comandante de CAI, no jerga de ML). Distinguir del registro técnico de los notebooks.

**Red flags que corregir:**
- Usar Claude API como modelo predictivo (viola el espíritu del concurso — XGBoost es el modelo)
- Usar validación aleatoria (train/test split random) en lugar de temporal — el split correcto es TRAIN = ene–oct 2025, TEST = nov 2025–abr 2026 (F5 NUSE solo disponible 2025–2026)
- Modelar por localidad en lugar de UPZ (demasiado grueso — 20 localidades vs 112 UPZs)
- Saltarse el análisis de sesgo por estrato en el Notebook 04 (el jurado siempre pregunta esto)
- Dejar el deploy de Streamlit Cloud para la última semana (hacerlo en Fase 3, no al final)
- Cargar el GeoJSON de Estratificación (FUENTE 7, 100K+ manzanas) sin pre-calcular el promedio por UPZ — agota la RAM de Colab gratuito

---

## Fechas críticas (2026)

| Fecha | Hito |
|-------|------|
| ✅ 23 mayo | Notebook 01 completado — plan + catálogo de 12 fuentes (F1-F10 activas + F11-F12 planificadas) |
| ✅ 26 mayo – 6 junio | **Fase 1:** EDA de las 10 fuentes → Notebook 02 ✅ |
| ⏳ 7 – 20 junio | **Fase 2:** XGBoost + SHAP → Notebooks 03+04 |
| ⏳ 21 junio – 10 julio | **Fase 3:** Dashboard Streamlit + Claude API → Notebook 05 |
| ⏳ 11 – 13 julio | **Fase 4:** Docs + video + registro → Notebook 06 |
| **13 julio** | **Entrega:** GitHub público + registro en datos.gov.co |
| 14–17 julio | Sustentación oral (10 minutos + preguntas) |

---

## Preguntas difíciles del jurado — respuestas preparadas

**"¿Su modelo discrimina por estrato?"**
→ Sí lo analizamos. El Notebook 04 incluye análisis de sesgo por estrato socioeconómico. El modelo usa estrato como variable pero los SHAP values permiten identificar si produce predicciones sistemáticamente sesgadas. PredPol en EE.UU. fue discontinuado por esto — nosotros lo prevenimos por diseño.

**"¿Qué pasa si el SIEDCO tiene subregistro?"**
→ Lo mitigamos de dos formas: (1) usamos el crimen reportado como proxy, explicitando la limitación, y (2) el ratio NUSE_123/delitos_formales_por_UPZ es un feature del modelo que captura el nivel de subregistro por zona. Barrera et al. (Uniandes 2023) es la referencia metodológica.

**"¿Cómo escala esto a otra ciudad?"**
→ La arquitectura es modular. Para replicar en otra ciudad: sustituir el dataset Socrata por el ID equivalente local, reemplazar los shapefiles de UPZ por la división administrativa local, y recalibrar los thresholds del modelo. El README documenta este proceso. Para Barranquilla se puede usar transfer learning preentrenado en Bogotá.

**"¿Cómo previenen el crimen, no solo lo predicen?"**
→ La capa prescriptiva diagnostica la causa raíz (temporal, estructural, urbanística) y mapea cada diagnóstico a la entidad distrital responsable de la intervención. No mandamos más policías — identificamos qué tipo de intervención necesita cada zona y quién debe ejecutarla.

**"¿Qué diferencia esto del Atlas del Crimen que ganó en 2025?"**
→ El Atlas del Crimen es análisis descriptivo — explica qué ha pasado históricamente. Este sistema es predictivo y prescriptivo. Además, el Atlas operó a nivel departamental sin modelo ML. Este proyecto opera a nivel UPZ con XGBoost + SHAP + FastAPI operacional.

---

## Decisiones de diseño ya tomadas (no reabrir sin justificación fuerte)

| Decisión | Justificación |
|----------|--------------|
| Solo Bogotá | Calidad de datos superior + volumen garantizado + no penalización por enfoque único |
| Granularidad UPZ (no localidad, no barrio) | Balance entre resolución y estabilidad estadística |
| Stack Python + scikit-learn + XGBoost | Reproducible, bien documentado, compatible con CRISP-ML |
| ~~Hawkes Process~~ → **GraphRAG causal** | Hawkes descartado por complejidad/tiempo. GraphRAG (nano-graphrag + Claude API) diferencia mejor: explica el *por qué* del crimen usando boletines SCJ + noticias + Plan Desarrollo |
| SHAP para interpretabilidad | Requerido para la capa prescriptiva y valorado por el jurado técnico |
| Streamlit para dashboard | Fácil de desplegar en Streamlit Cloud, no requiere backend separado |
| `wiki_pages/` como fuente única de docs | Editar wiki_pages/ + correr PUSH_WIKI.bat → wiki actualizado. El código solo tiene README, CLAUDE.md y CRONOGRAMA.md |
