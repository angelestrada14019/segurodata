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
| ¿Qué está pasando? | 1 — Diagnóstico | React + deck.gl + Supabase Realtime |
| ¿Qué va a pasar? | 2 — Predicción | XGBoost + SHAP + ruptures (cambios estructurales) |
| ¿Qué hacer? | 3 — Recomendación | Tabla ontológica + OpenRouter (Gemini Flash) |
| ¿Por qué? | 4 — Chatbot causal | FastAPI + Supabase pgvector + OpenRouter |

---

## Stack técnico

| Capa | Tecnologías |
|------|------------|
| Ingesta y limpieza | `polars`, `geopandas`, `requests` |
| Análisis espacial | `geopandas`, `shapely` |
| Modelo ML | `xgboost`, `scikit-learn`, `shap`, `ruptures` |
| Change point detection | `ruptures` (PELT sobre DAI histórico 2018–2026) |
| Embeddings (GraphRAG) | `sentence-transformers` — `all-MiniLM-L6-v2` (local, gratis, 384 dims) |
| LLM / GraphRAG | **OpenRouter** — `google/gemini-flash-1.5` (gratis 1M tokens/día) como primaria; `anthropic/claude-haiku` como fallback |
| Base de datos | **Supabase** (PostgreSQL + PostGIS + pgvector) |
| Backend ML | **FastAPI** (Python) en **Railway** — GraphRAG + prescriptivo + proxy OpenRouter |
| Frontend / mapa | **React + Vite + deck.gl + Tailwind CSS** |
| Deploy frontend | **Vercel** (React, CDN global, siempre activo) |
| Deploy backend | **Railway** (FastAPI, siempre activo, sin cold start, ~$5/mes plan Hobby) |
| Repositorio | GitHub (público, obligatorio para el concurso) |

**No hay Streamlit, no hay cron externo, no hay Edge Functions Deno, no hay nano-graphrag.**  
- **Demo + producción:** un único backend Python (FastAPI en Railway). El frontend llama Supabase directamente para datos y FastAPI para GraphRAG + prescriptivo.  
- **Railway es siempre activo** — no requiere calentamiento previo ni warmup antes del demo.

---

## Las 12 fuentes de datos activas (+ F12 planificada)

| # | Fuente | Plataforma | Rol en el modelo |
|---|--------|-----------|-----------------|
| F1 | Delito de Alto Impacto — Sec. Seguridad | CKAN — descarga ZIP | EDA histórico 2018–2026 + **ruptures** (cambios estructurales por localidad) |
| F2 | UPZ Shapefile — IDECA | ArcGIS REST | Base espacial — spatial joins |
| F3 | Open-Meteo — Clima Bogotá | REST API (sin clave) | Features climáticas |
| F4 | Cuadrantes de Policía — MEBOG | CKAN — descarga ZIP | Feature cobertura policial + conexión CAI |
| F5 | Incidentes NUSE 123 — C4 | CKAN Datastore API | **BASE Silver**: genera 111,606 filas × 20 cols |
| F6 | Hurto Personas — Policía Nacional | Socrata `4rxi-8m8d` | Benchmarking nacional — contexto oral |
| F7 | Estratificación por manzana — SDP | CKAN — URL directa | Feature socioeconómica + análisis sesgo |
| F8 | Estaciones TransMilenio — TM S.A. | ArcGIS REST | Features movilidad/afluencia |
| F9 | Boletines SCJ — Sec. Distrital Seguridad | scj.gov.co (PDFs) | Corpus GraphRAG → pgvector (Supabase) |
| F10 | Noticias RSS — El Tiempo / Espectador / El Informante Soy Yo | RSS público (3 feeds verificados) | Corpus GraphRAG → pgvector (Supabase) |
| **F11** | **Malla Vial + Obras IDU activas** | **IDECA / datosabiertos.bogota.gov.co** | **Feature km_via_intervenida_upz → XGBoost** |
| **F13** | **Cámaras Salvavidas SDM** | **ArcGIS Hub SDM** | **Feature n_camaras_upz + capa visual deck.gl** |
| **F14** | **Alumbrado Público UAESP por UPZ** | **CKAN Bogotá** | **Feature luminarias_led_upz → XGBoost** |

> **F12 (Plan Desarrollo Bogotá 2024-2027)** se planifica para Fase 3 (corpus GraphRAG).  
> **Silver actual**: 111,606 filas × 20 cols. Con F11+F13+F14 → 23 columnas (3 features nuevas).  
> F1/F6 no tienen desglose UPZ pero F1 se usa con **ruptures** para detección de puntos de cambio históricos.

**Investigación completa de 20+ fuentes** (incluyendo descartadas) en el [Wiki — Investigacion-Fuentes](https://github.com/angelestrada14019/segurodata/wiki/Investigacion-Fuentes) y `docs/fuentes_validadas.xlsx`.

---

## Las 18 variables del modelo XGBoost

> Granularidad **UPZ × mes** (agregado mensual por zona, no a nivel evento). Lista real en `scripts/train_model.py` (constante `FEATURES`).

```
HISTÓRICAS / LAG TEMPORAL:
  n_delitos_upz_4sem      ← delitos del mes previo (lag-1) por UPZ
  n_delitos_upz_8sem      ← delitos acumulados últimos 2 meses por UPZ
  n_delitos_upz_12sem     ← delitos acumulados últimos 3 meses por UPZ
  tendencia_upz           ← momentum: lag1 − lag2 (sube/baja mes a mes)

LAG ESPACIAL:
  n_delitos_vecinos_lag   ← promedio de delitos de UPZs vecinas en t-1 (adyacencia shapefile F2)

TEMPORALES CÍCLICAS:
  mes_sin / mes_cos       ← codificación cíclica del mes (dic y ene quedan adyacentes)

CLIMÁTICAS (Open-Meteo):
  temperatura_c           ← temperatura °C promedio del mes
  precipitacion_mm_mes    ← precipitación mm acumulada del mes

ESPACIALES:
  estrato_promedio_upz    ← promedio ponderado del estrato por manzana
  cuadrantes_por_km2      ← densidad de cuadrantes policiales en la UPZ
  n_estaciones_tm         ← número de estaciones TM dentro de la UPZ
  dist_tm_metros          ← distancia del centroide de la UPZ a la TM más cercana

SUBREGISTRO:
  ratio_nuse_criminal_upz ← fracción de llamadas NUSE que son crimen / total por UPZ·mes

INFRAESTRUCTURA (F11, F13, F14 — placeholder=0 hasta que existan los extractores):
  km_via_intervenida_upz  ← kilómetros de vía con obra IDU activa en la UPZ
  n_camaras_upz           ← número de cámaras Salvavidas SDM en la UPZ
  luminarias_led_upz      ← número de luminarias LED (iluminación pública UAESP)

TIPO DE DELITO:
  tipo_crimen_cod         ← tipo de delito dominante en la UPZ (codificado a entero)

VARIABLE OBJETIVO (Y):
  nivel_riesgo: CRÍTICO / ALTO / MEDIO / BAJO
  → percentiles de n_delitos por upz_cod × anio × mes (solo es_crimen=True):
    ≥q95 = CRÍTICO · ≥q75 = ALTO · ≥q40 = MEDIO · resto = BAJO
  → distribución: BAJO=811, MEDIO=735, ALTO=392, CRÍTICO=100 (2,038 filas)

MÉTRICAS (test temporal dic 2025 – may 2026, 719 filas — ver datos/modelos/metricas.json):
  banda exacta 0.871 · dentro de ±1 banda 100% · macro-F1 0.861 · recall CRÍTICO 0.92
  → nivel_riesgo es ORDINAL: la métrica defendible es el acierto dentro de ±1 banda
    (cero saltos de clase). El error de banda exacta restante es ruido de frontera
    entre percentiles, irreducible. NO perseguir 95% exact-match (ver memoria del proyecto).
  → El split temporal es DINÁMICO (scripts/train_model.py::_calcular_corte_train_test):
    TEST = últimos 6 meses con datos disponibles, TRAIN = el resto. Se recalcula en
    cada reentrenamiento — estos números avanzan solos a medida que llegan datos
    nuevos, no son una foto fija de una sola corrida.
```

---

## Estructura de carpetas

```
proyecto/
├── datos/
│   ├── raw/              ← Bronze: archivos como se descargan (generados por pipeline.py)
│   │   └── boletines_scj/← F9: PDFs descargados de SCJ
│   ├── procesados/       ← Silver: datos limpios y unificados (generados por transform.py)
│   ├── features/         ← Gold: tabla maestra UPZ con las 18 variables (scripts/train_model.py)
│   ├── grafo/            ← GraphRAG: embeddings pgvector exportados para Supabase
│   └── modelos/          ← Model: XGBoost + SHAP pre-computado (Notebook 04)
├── graficas/             ← Outputs visuales del EDA (7 gráficas V1-V7)
├── src/
│   ├── etl.py            ← 4 conectores de bajo nivel: CKAN, Socrata, ArcGIS, Open-Meteo
│   ├── pipeline.py       ← Extracción incremental Bronze (12 fuentes F1-F14)
│   ├── transform.py      ← Transformación Silver (limpieza + spatial joins)
│   └── validar_fuentes.py← genera fuentes_validadas.xlsx con fuentes activas
├── backend/              ← FastAPI (Python) — inferencia ML: /predict /explain /query
│   ├── main.py
│   ├── routers/          ← predict.py, explain.py, graphrag.py
│   └── requirements.txt  ← fastapi, xgboost, shap, langchain-anthropic
├── frontend/             ← React + Vite + deck.gl
│   ├── src/
│   │   ├── components/   ← MapView, PrescriptivoPanel, ChatBot
│   │   └── pages/        ← Diagnostico, Prediccion, Prescriptivo, Chat
│   └── package.json
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
- `SeguroData_02_EDA.ipynb` — Diagnóstico descriptivo + change points F1 DAI ✅
- `SeguroData_03_Features.ipynb` — Construcción de las 18 variables (F11+F13+F14) + tabla prescriptiva
- `SeguroData_04_Modelo.ipynb` — XGBoost + backtesting + SHAP pre-computado + sesgo
- `SeguroData_05_Dashboard.ipynb` — Arquitectura React+FastAPI+Supabase + screenshots
- `SeguroData_06_Deployment.ipynb` — Deploy Railway+Vercel + registro datos.gov.co

---

## El diferenciador clave

Todos los equipos predirán crimen. Lo que distingue a SeguroData:

> *"No solo predice dónde habrá delitos — le dice exactamente a qué cuadrante de la Policía tiene que ir y por qué. Ese es el puente que hoy no existe entre los datos abiertos de Bogotá y la acción institucional."*

El Módulo 3 usa SHAP para identificar la causa dominante del riesgo y conecta directamente con el CAI responsable — sin esto, la predicción es descriptiva, no operativa.

---

## Cómo ayudar en este proyecto

> **🔒 Regla inamovible — documentación:** tras CUALQUIER cambio en código, datos o arquitectura, **pregunta al usuario si desea actualizar la documentación** (`wiki_pages/`, `README.md`, `CLAUDE.md`, `CRONOGRAMA.md`) antes de cerrar la tarea. La documentación de cara al jurado se presenta como **estado final**, sin comparativas antes/después.

**Cuando el usuario traiga código:** revisar con énfasis en correctitud, reproducibilidad en Colab, y eficiencia con datasets grandes. Los dos datasets más pesados: F6 Hurto PN (638K filas, solo benchmarking) y F7 Estratificación (44K polígonos de manzanas — el spatial join agota RAM en Colab gratuito).

**Cuando pida análisis:** usar el contexto de Bogotá — 112 UPZs, localidades, las 12 fuentes activas (F1-F14). No generalizar.

**Cuando pida texto para el chatbot o recomendaciones:** el Módulo 3 y 4 usan OpenRouter (modelo configurable via `LLM_MODEL` — por defecto `google/gemini-flash-1.5`). Los mensajes son operacionales (lenguaje del comandante de CAI, no jerga de ML). Distinguir del registro técnico de los notebooks.

**Red flags que corregir:**
- Usar Claude API como modelo predictivo (viola el espíritu del concurso — XGBoost es el modelo)
- Usar validación aleatoria (train/test split random) en lugar de temporal — TRAIN = ene–oct 2025, TEST = nov 2025–abr 2026 (F5 NUSE solo disponible 2025–2026)
- Modelar por localidad en lugar de UPZ (demasiado grueso — 20 localidades vs 112 UPZs)
- Saltarse el análisis de sesgo por estrato en el Notebook 04 (el jurado siempre pregunta esto)
- Usar Streamlit como frontend principal del dashboard — el frontend es React + deck.gl
- Calcular SHAP on-demand en la app — los SHAP values se pre-computan en Notebook 04 y se sirven desde Supabase
- Proponer nano-graphrag o Microsoft GraphRAG — el stack es FastAPI + Supabase pgvector + OpenRouter
- Agregar una fuente nueva sin pasar por la regla de investigación quirúrgica (ver sección abajo)
- Cargar el GeoJSON de Estratificación (F7, 100K+ manzanas) sin pre-calcular el promedio por UPZ — agota la RAM de Colab gratuito

---

## Fechas críticas (2026)

| Fecha | Hito |
|-------|------|
| ✅ 23 mayo | Notebook 01 completado — plan + catálogo de 12 fuentes (F1-F10 activas + F11-F12 planificadas) |
| ✅ 26 mayo – 6 junio | **Fase 1:** EDA de las 10 fuentes → Notebook 02 ✅ |
| ✅ 10 junio | Arquitectura pivotada a React+Supabase+FastAPI · F13/F14 activadas · Wiki publicado (13 páginas + Plataforma-Ciudadana) · GitHub Project poblado (issues #11-18) · Plataforma ciudadana: ideas 1+2+3+5 comprometidas para MVP, ideas 4+6 opcionales con HUs en `docs/HU-Features-Opcionales.md`, idea 7 descartada · Pre-mortem documentado |
| ✅ 7 – 20 junio | **Fase 2:** XGBoost + SHAP → Notebooks 03+04 (vía script `train_model.py`) |
| ✅ 21 junio – 10 julio | **Fase 3:** React+deck.gl + FastAPI + GraphRAG Supabase — 4 módulos + modal de 5 pestañas + Panel Admin + deploy Railway/Vercel, todo en producción → Notebook 05 (⏳ wrapper visual opcional) |
| ⏳ 11 julio – 1 agosto | **Fase 4:** Docs + video + registro datos.gov.co → Notebook 06 (deploy ya completado en Fase 3) |
| **⚠️ Verificar** | Fecha exacta entrega/registro en datos.gov.co — posiblemente agosto (GovCamps 2026) |
| Primera semana agosto | **Final GovCamps 2026** (sustentación oral — confirmado MinTIC) |

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

**"¿Cómo mantienen el modelo actualizado con datos nuevos?"**
→ Pipeline automatizado en GitHub Actions (`.github/workflows/etl-semanal.yml`, disparo manual hoy, cron semanal desactivado hasta después de la sustentación): descarga incremental → Silver → reentrena XGBoost con una ventana temporal *dinámica* (últimos 6 meses = test, se recalcula sola con cada corrida, no una fecha fija) → un quality-gate compara macro-F1 y accuracy ±1 banda contra umbrales mínimos antes de tocar producción — si el modelo nuevo es peor, el pipeline se detiene solo y Supabase no se toca. `metricas.json` queda versionado en git como historial verificable de performance en el tiempo.

**"¿Qué diferencia esto del Atlas del Crimen que ganó en 2025?"**
→ El Atlas del Crimen es análisis descriptivo — explica qué ha pasado históricamente. Este sistema tiene tres capas: descriptivo (mapa interactivo en tiempo real), predictivo (XGBoost + SHAP por UPZ), y prescriptivo real (ruptures detecta cuándo cambia el patrón + GraphRAG identifica la causa + tabla ontológica mapea a la entidad responsable). El Atlas operó a nivel departamental sin modelo ML ni capa prescriptiva.

---

## Decisiones de diseño ya tomadas (no reabrir sin justificación fuerte)

| Decisión | Justificación |
|----------|--------------|
| Solo Bogotá | Calidad de datos superior + volumen garantizado + no penalización por enfoque único |
| Granularidad UPZ (no localidad, no barrio) | Balance entre resolución y estabilidad estadística |
| Stack Python + scikit-learn + XGBoost | Reproducible, bien documentado, compatible con CRISP-ML |
| ~~Hawkes Process~~ → **ruptures + GraphRAG** | Hawkes descartado. ruptures (PELT) detecta cambios estructurales históricos. GraphRAG (FastAPI + pgvector + OpenRouter) explica el *por qué* con boletines SCJ + noticias |
| SHAP pre-computado (no on-demand) | Supabase sirve SHAP values pre-calculados → sin crash de RAM en producción |
| **React + deck.gl** para frontend | Mapa WebGL interactivo estilo C4 / Palantir Gotham, capas toggleables, zoom Localidades→UPZs (zoom 12), modal 5 pestañas por UPZ (Descripción · Predicción · Sugerencia · Fuentes · Chatbot) |
| **Reentrenamiento con quality-gate, sin cron activo** | `scripts/load_model_artifacts.py` nunca sobreescribe con un modelo peor sin `--force` explícito. El workflow de GitHub Actions corre la cadena completa bajo demanda (`workflow_dispatch`); el `schedule` semanal queda comentado a propósito hasta después de la sustentación oral — evita que un reentrenamiento automático caiga en medio del demo |
| **Supabase** como backbone | PostgreSQL + PostGIS + pgvector en un solo servicio. El frontend lo consulta directamente para datos, predicciones y SHAP |
| **FastAPI + Railway** | Backend Python unificado: GraphRAG + prescriptivo + proxy OpenRouter. Siempre activo, sin cold start, un solo deploy. Railway Plan Hobby ~$5/mes |
| **OpenRouter** como proxy LLM | Una API key da acceso a 200+ modelos. Demo: Gemini Flash (gratis). Producción: escalable |
| **sentence-transformers** para embeddings | all-MiniLM-L6-v2, corre local una sola vez, resultado se guarda en pgvector. Sin costo de API |
| **Supabase Auth + RLS** para control de acceso | 4 roles: CIUDADANO · COMANDANTE_CAI · ANALISTA_SDSCJ · ADMIN. Magic link + autoprovisioning por dominio @policia.gov.co. RLS filtra predicciones por cuadrante asignado usando F4 Cuadrantes en PostGIS. SHAP ciudadano=básico/analista=completo. |
| **Plataforma Ciudadana (ideas 1+2+3+5) comprometidas** | Auth+Roles, mapa zoom adaptativo Localidades→UPZs, modal 5 pestañas, proyección +4 semanas en Módulo 2. Ideas 4+6 opcionales (HUs en `docs/HU-Features-Opcionales.md`). Idea 7 (app nativa) descartada para el concurso. |
| `wiki_pages/` como fuente única de docs | Editar wiki_pages/ + correr PUSH_WIKI.bat → wiki actualizado. El código solo tiene README, CLAUDE.md y CRONOGRAMA.md |

---

## Regla de fuentes quirúrgicas (obligatoria antes de agregar cualquier fuente)

Antes de proponer o agregar una fuente nueva, documentar este checklist completo:

```yaml
fuente_candidata:
  nombre: ""
  url_descarga: ""
  granularidad: ""           # UPZ / localidad / municipio / punto — ¿tiene UPZ?
  ultima_actualizacion: ""   # ¿está activa? ¿cuándo fue la última actualización?
  contribucion_modelo: ""    # ¿qué feature nueva agrega al XGBoost?
  contribucion_mapa: ""      # ¿aparece como capa en deck.gl?
  licencia: ""               # CC BY 4.0, pública, privada
  esfuerzo_horas: 0          # estimado realista de integración
  evidencia_causal: ""       # paper o dato empírico que justifica la relación con crimen
  decision: ACTIVAR | PLANIFICAR | DESCARTAR
  justificacion: ""          # razón de la decisión
```

**Fuentes descartadas automáticamente** (sin necesidad de checklist):
- Granularidad solo municipio o departamento (sin desglose UPZ)
- APIs de pago o scraping de redes sociales (viola reglas concurso)
- Datos privados o de vigilancia con restricción legal (Ley 1581/2012)
- Esfuerzo > 2 semanas sin contribución diferencial clara
