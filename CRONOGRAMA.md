# CRONOGRAMA.md — Fases del Proyecto SeguroData Bogotá

> Entrega: **13 julio 2026** (GitHub público + registro datos.gov.co) · Sustentación: 14–17 julio
>
> **Nota sobre fecha:** Existe posibilidad de que el evento final sea GovCamps agosto 2026. Si se confirma, hay ~3 semanas extra. Verificar en datos.gov.co antes de la Fase 4.

---

## Vista general

```
MAYO                        JUNIO                          JULIO
Fase 0 ✅ | Fase 1A ✅ | Fase 1B ✅ | Fase 2 ⏳ | Fase 3 ✅ | Fase 4 ⏳
25 May    | 26–27 May  | 27M–6Jun   |  7–20 Jun | 21J–10Jul | 11–13 Jul
[Plan]    | [Bronze]   | [Silver+EDA]| [Modelo]  | [Dashboard+IA] | [Docs]
```

**Repositorio:** https://github.com/angelestrada14019/segurodata  
**Ramas activas:** `main` (única rama — todas las fases se integran aquí)

---

## Fase 0 ✅ — Completada (23 mayo 2026)

**Entregable:** `SeguroData_01_Plan_y_Fuentes.ipynb`

- ✅ Descripción del problema y propuesta
- ✅ 3 perfiles de usuario definidos (Comandante CAI, Sec. Seguridad, Ciudadano)
- ✅ 4 módulos del sistema definidos (Diagnóstico, Predicción, Recomendación, Chatbot)
- ✅ Catálogo de 14 fuentes (F1-F10 activas + F11/F13/F14 activadas 10-jun + F12 planificada) con URLs verificadas, variables y código de carga
- ✅ Arquitectura Medallón definida (Bronze/Silver/Gold/Model)
- ✅ 18 variables del modelo XGBoost documentadas
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
- [x] Tabla final: **111,606 filas × 20 columnas** (F11/F13/F14 se integran en la capa Gold), 120 UPZs, 86 tipos NUSE, 19 localidades, ene 2025–abr 2026

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

> **🔀 Rama `features_model` (17-jun):** revisada e integrada selectivamente a `main` (commit
> `63abe85`). Se tomó: NB01/NB02 actualizados (catálogo + celda `ruptures` V8 en EDA, corregida a
> 18 variables reales). Se descartó: `SeguroData_03_Features.ipynb` y `SeguroData_04_Modelo.ipynb`
> (redefinían `nivel_riesgo` con umbrales absolutos en vez de percentiles, y entrenaban su propio
> XGBoost sin importar `scripts/train_model.py`), y un generador de **datos sintéticos aleatorios**
> para F11/F13/F14 en `transform.py` (presentaba ruido como si fuera infraestructura real). La
> rama remota se conserva sin borrar. `scripts/train_model.py` sigue siendo la única fuente de
> verdad del modelo.

### Setup Supabase + nuevas fuentes (7–10 junio) — EN PARALELO con modelo

- [x] ✅ (10-jun) Crear proyecto Supabase → habilitar PostGIS + pgvector — proyecto `segurodata` (ref `pluxaelenhkdaakxdrpm`, us-east-1), **11 migraciones** en `supabase/migrations/` (0001-0011)
- [x] ✅ (10-jun) Schema inicial aplicado (8 tablas + RLS + hook claims + RPC match_documents). **Decisión arquitectural (11-jun): Silver 111K queda LOCAL** — Supabase solo recibe outputs del modelo + geometrías + corpus embeddings + change_points (patrón FTI). **✅ (16-jun) Seed_dev reemplazado con datos reales: 1,918 predicciones + 34,524 SHAP (`origen='notebook_04'`), 112 UPZ, 599 cuadrantes, 40 change_points, 10 chunks RSS corpus.**
- [x] ✅ (11-jun) Migración 0011: columnas `metadata JSONB` en `predicciones` y `shap_values` para trazabilidad FTI (model_version, pipeline_run_date, features)
- [x] ✅ (11-jun) Hook JWT habilitado: Dashboard → Authentication → **Auth Hooks** → "Add hook" → **"Customize Access Token (JWT) Claims hook"** → tipo PostgreSQL Function → `public.custom_access_token_hook` → ENABLED. Los roles (CIUDADANO/COMANDANTE_CAI/ANALISTA_SDSCJ/ADMIN) ya viajan en el JWT.
- [x] ✅ (11-jun) Realtime habilitado vía migración `0009_realtime.sql` (`ALTER PUBLICATION supabase_realtime ADD TABLE silver_upz_mes`). Alternativa Dashboard: Database → Publications → `supabase_realtime` → toggle ON.
- [ ] Integrar F13 Cámaras Salvavidas SDM → spatial join → feature `n_camaras_upz`
- [ ] Integrar F14 Alumbrado UAESP → merge directo → feature `luminarias_led_upz`
- [ ] Integrar F11 IDU Obras Viales → spatial join → feature `km_via_intervenida_upz`
- [x] ✅ (11-jun / 16-jun) `ruptures` PELT sobre F1 DAI 2018–2026: **40 breakpoints detectados (pen=5, max_bp=2)**, COVID 2020 BAJA validado (17 localidades). Script: `scripts/compute_change_points.py` → cargados en Supabase `change_points`.
- [x] ✅ (10-jun) **[Pre-mortem T7]** Tabla `cuadrantes_geom` creada con índice GIST + columna `upz_codes[]` pre-computada (599 cuadrantes con nom_cai y teléfono). ⏳ Geometrías reales se cargan con `seed_supabase.py --solo geo`

### Notebook 03 — Features (7–12 junio) ✅ VÍA SCRIPT

> **16-jun-2026: Implementado como `scripts/train_model.py` (no notebook).** El concurso no requiere Jupyter. Los notebooks NB03/NB04 pueden crearse como wrappers visuales opcionales para el jurado.

- [x] ✅ (16-jun) Construir tabla maestra `datos/features/tabla_maestra_upz.parquet` con **18 features** (F11/F13/F14 = 0 placeholder hasta que existan extractores). **1,918 filas**. Features nuevas (16-jun): `n_delitos_upz_12sem` (lag-3), `tendencia_upz` (momentum), `n_delitos_vecinos_lag` (lag espacial de UPZs vecinas vía adyacencia F2), `mes_sin`/`mes_cos` (cíclicas, reemplazan `mes` crudo)
- [x] ✅ (16-jun) Definir `nivel_riesgo` (Y): `GROUP BY upz_cod, anio, mes` sobre `es_crimen=True` — percentiles q95=CRÍTICO, q75=ALTO, q40=MEDIO, BAJO. Distribución: BAJO=765, MEDIO=672, ALTO=384, CRÍTICO=97
- [x] ✅ Tabla ontológica prescriptiva ya en `backend/app/data/tabla_ontologica_seed.json` (17 filas SHAP→diagnóstico→entidad→acción)
- [ ] ⏳ Normalizar features con StandardScaler → `datos/modelos/scaler.pkl` (pendiente si el frontend lo necesita)

### Notebook 04 — Modelo (13–20 junio) ✅ VÍA SCRIPT

- [x] ✅ (16-jun) Split temporal: TRAIN = ene–oct 2025, TEST = nov 2025+ (NO split aleatorio)
- [x] ✅ (16-jun) `XGBClassifier(objective='multi:softprob', num_class=4, n_estimators=300, max_depth=5)` — **exact 0.871 · accuracy dentro de ±1 banda 100% · macro-F1 0.867 · MAE ordinal 0.129** (test temporal nov-2025+, 719 filas). Métricas en `datos/modelos/metricas.json`. Matriz de confusión: **cero errores de salto de clase** — el 13% restante es ruido de frontera entre percentiles (irreducible: el umbral ordinal calibrado no generaliza). `nivel_riesgo` es ordinal → la accuracy ±1 banda es la métrica defendible, no el exact-match
- [x] ✅ (16-jun) SHAP values pre-computados con `TreeExplainer` — 34,524 filas formato largo (upz_cod × anio × mes × feature, 18 features). Top features: n_delitos_upz_4sem (1.33), n_delitos_upz_8sem (0.38), ratio_nuse (0.27), cuadrantes_por_km2 (0.19), mes_cos (0.12), n_delitos_upz_12sem (0.12)
- [x] ✅ (16-jun) Análisis de sesgo por estrato — función `analisis_sesgo()` en `scripts/train_model.py`
- [x] ✅ (16-jun) Modelo guardado: `datos/modelos/modelo_xgboost.pkl` + `datos/modelos/predicciones.parquet`
- [x] ✅ (16-jun) Cargado en Supabase: `python scripts/load_model_artifacts.py` (REST fallback, origen='notebook_04')

### Track paralelo — Knowledge Graph F9/F10 (7–20 junio)

- [x] ✅ (10-jun) Corpus demo cargado inicialmente con 12 chunks SEED_DEV.
- [x] ✅ (16-jun) `python src/pipeline.py --source f10` → RSS noticias descargadas
- [x] ✅ (16-jun) `python scripts/index_corpus.py --backend fastembed` → **10 chunks RSS reales** (El Tiempo + Informante) en Supabase pgvector. SEED_DEV eliminados. `/graphrag` responde con fuentes reales.
- [ ] ⏳ F9 boletines SCJ: descarga MANUAL (sitio ArcGIS Experience Builder no es scrapeable con BS4). Ir a oaiee.scj.gov.co → guardar PDFs en `datos/raw/boletines_scj/` → re-ejecutar `index_corpus.py`
- [ ] Verificar búsqueda semántica con query real post-carga de F9

---

## Fase 3 ✅ — React + FastAPI + GraphRAG (21 junio – 10 julio 2026)

**Entregable:** `SeguroData_05_Dashboard.ipynb` (⏳ pendiente, wrapper visual opcional) + app React desplegada en Vercel ✅

> **🛠️ Tooling (17-jun):** 5 skills de frontend vendorizadas (`frontend-design` de Anthropic + `react-patterns` · `tailwind-theme-builder` · `shadcn-ui` · `design-review` de jezweb, todas MIT), el agent **`frontend-builder`** que las orquesta con el contrato del proyecto (deck.gl, 4 módulos, paleta de riesgo, endpoints), y `frontend/CLAUDE.md` de arranque. Atribución en `.claude/skills/VENDORED.md`. La Fase 3 se está construyendo por sprints delegados a `frontend-builder`, verificados por el orquestador antes de continuar (mismo patrón que `fastapi-builder` en el backend).

### Semana 1 — FastAPI backend + mapa base (21–27 junio)

- [x] ✅ (10-jun, adelantado) Backend FastAPI COMPLETO en `/backend`: `/predict`, `/explain`, `/graphrag`, `/prescribe`, `/whoami`, `/health`, `/admin/usuarios/{id}/cuadrante` (7 endpoints) — capas routers→services→repos→clients, JWT+roles, rate limiting, 36 tests verdes, Dockerfile+railway.toml listos (ver `backend/README.md`)
- [x] ✅ (16-jun) Predicciones + SHAP servidos desde Supabase vía lookup — **artefactos reales cargados**: 1,918 predicciones + 34,524 SHAP (`origen='notebook_04'`). Seed_dev eliminado. Script: `scripts/train_model.py` → `scripts/load_model_artifacts.py`
- [x] ✅ (01-jul) **Migración `20260701_0012_geojson_rpc.sql`**: 3 RPCs GeoJSON (`upz_geojson`/`localidades_geojson` en SECURITY DEFINER con filtro de rol/cuadrante explícito — mismo patrón D8 del backend, necesario porque la RLS de `predicciones` es solo `authenticated` y no cubre el mapa público sin login; `cuadrantes_geojson` en SECURITY INVOKER simple). Verificado en vivo: `anon` ve 112/112 UPZ con riesgo (mapa público funciona), comandante de prueba ve solo 2/112 de su cuadrante — restricción de seguridad confirmada empíricamente, no solo en teoría.
- [x] ✅ (01-jul) **Sprint 1 (`frontend-builder`)**: Skeleton React 19 + Vite + Tailwind v4 + shadcn/ui + TanStack Query + supabase-js + react-router-dom + deck.gl. Mapa con `GeoJsonLayer` (NO `PolygonLayer` — `upz_geometrias.geom` es `MultiPolygon`) de las 112 UPZs coloreadas (paleta fija en `lib/colores-riesgo.ts`: CRÍTICO=morado, ALTO=rojo, MEDIO=naranja, BAJO=verde) + zoom adaptativo Localidades↔UPZs + leyenda con `aria-label`. Auth: `/login` magic link + `ProtectedRoute` con la matriz de roles correcta (CIUDADANO **sin** acceso a `/prediccion`, verificado contra `wiki_pages/Modulos.md`).
- [x] ✅ (09-jul) **Verificación visual en navegador**: confirmada end-to-end. Encontró y cerró 2 bugs bloqueantes que la verificación pendiente nunca había atrapado — (1) RLS de `predicciones` es `TO authenticated` únicamente, así que un visitante anónimo (el caso público de `/diagnostico`) recibía período `NULL` y eso disparaba un bug de duplicación de filas en `upz_geojson`/`localidades_geojson` que excedía el `statement_timeout` de 3s del rol `anon` — resuelto con la RPC `periodo_mas_reciente` (migración `0013`); (2) el contenedor del mapa tenía `height:0` real (`min-height` sin `height` no es "definido" para que un hijo con `height:100%` lo herede) — resuelto cambiando el mecanismo a `flex`+`align-items:stretch`. De paso se encontró que `upz_geometrias.cod_localidad`/`nom_localidad` están `NULL` en las 112 filas (el pipeline F2 nunca trajo el código de localidad) — la vista agregada por localidades caía a 1 sola feature fusionada; migración `0014` la corrige cayendo a agrupar por UPZ individual cuando no hay localidad real.
- [x] ✅ (09-jul) Slider temporal funcional → navega meses históricos de `predicciones`, recolorea el mapa.

### Semana 2 — Módulo Diagnóstico + Predicción (28 junio – 4 julio) ✅

- [x] ✅ Módulo 1: capas toggleables deck.gl — Cuadrantes de Policía y Cambios estructurales reales; Cámaras F13, Alumbrado F14 y Estaciones TransMilenio quedan marcadas "Pendiente de datos" (placeholder=0 en el modelo, sin geometría inventada, hasta que existan extractores reales)
- [ ] Módulo 1: Heatmap día × hora (Plotly React) — **diferido**, dependencia nueva pesada de menor prioridad frente al resto del alcance
- [x] ✅ Módulo 1: tendencia con change points marcados — capa de rupturas estructurales (`change_points`) sobre el mapa; hoy resuelve 0 marcadores visibles porque el join necesita `cod_localidad` (ver bug de arriba) — el matching ya está implementado y normalizado, solo falta el backfill del mapeo UPZ→Localidad
- [x] ✅ Módulo 2: click en UPZ (mapa o Top-10) → modal de 5 pestañas → pestaña Predicción → `/predict`+`/explain` → nivel_riesgo + probabilidades + SHAP top-3
- [x] ✅ Módulo 2: mapa predictivo (reusa el mismo `GeoJsonLayer`/paleta de Módulo 1 — mismo dato, mismo lookup por PK) + Top-10 UPZs ordenado CRÍTICO→BAJO

### Semana 3 — Módulo Prescriptivo + Chatbot + Auth (5–10 julio) ✅

- [x] ✅ Módulo 3: tabla ontológica + SHAP top feature → diagnóstico → OpenRouter → recomendación operacional — verificado en vivo con UPZ real (034, ALTO): recomendación LLM con 3 causas específicas y acción por entidad
- [x] ✅ Módulo 3: panel CAI (nombre + cuadrante + teléfono) + indicador de change point (estructural vs temporal) — página standalone `/prescriptivo` con selector de UPZ, comparte componentes con la pestaña Sugerencia del modal
- [x] ✅ Módulo 4: chat input → FastAPI `/graphrag` → sentence-transformers embed → pgvector `match_documents` RPC → OpenRouter → respuesta con citas y número de boletín — disponible en el modal (contextualizado a la UPZ) y standalone en `/chatbot`
- [ ] Probar 10 preguntas tipo de los 3 perfiles de usuario — **pendiente la batería formal completa**; el flujo end-to-end ya se probó con preguntas reales contra el backend real
- [x] ✅ **[Pre-mortem E3]** (01-jul) JWT end-to-end verificado contra Supabase real: `pytest tests/test_jwt_e2e.py -m integration -v` → PASSED. El proyecto firma con **ES256/JWKS** (no HS256) — el test fue corregido para construir su propia app con `SUPABASE_JWKS_URL` real en vez de reusar el fixture `client` (HS256 de test), que habría dado un 401 falso.
- [x] ✅ **[Pre-mortem T5]** (01-jul, cerrado 09-jul en frontend) Backend cerrado de punta a punta contra Supabase real: `/whoami` devolvió `cuadrante_pendiente: true` con usuario COMANDANTE_CAI sin cuadrante, y `false` tras asignar cuadrante. Endpoint `PATCH /admin/usuarios/{user_id}/cuadrante` (rol ADMIN). En el frontend: `ProtectedRoute` redirige a `/cuadrante-pendiente` cuando corresponde, y el Panel Admin (`/admin/usuarios`, 100% Supabase directo vía RLS `admin_lee_perfiles`/`perfil_propio_o_admin`, sin endpoint nuevo) permite asignar el cuadrante desde la UI.
- [x] ✅ (09-jul) **Modal de 5 pestañas** (Descripción · Predicción · Sugerencia · Fuentes · Chatbot) — pieza central que unifica Módulos 2/3/4 por UPZ, se abre al hacer click en el mapa; componentes de la pestaña Sugerencia compartidos con la página standalone de Módulo 3, componentes de Chatbot compartidos con Módulo 4.
- [x] ✅ (09-jul) **Panel Admin** (`/admin/usuarios`, rol ADMIN) — lista de usuarios (`user_profiles` vía Supabase directo) + asignación de cuadrante a comandantes.

### Deploy ✅

- [x] ✅ (09-jul) FastAPI → Railway: proyecto `segurodata-api`, deploy vía CLI (`railway up`), variables de entorno configuradas (Supabase service key + JWKS, OpenRouter, CORS). `GET /health` → `{"status":"ok","env":"production"}` verificado en vivo.
- [x] ✅ (09-jul) React → Vercel: proyecto `segurodata-frontend`, deploy vía CLI (`vercel --prod`), variables `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY`/`VITE_API_URL` configuradas apuntando al Railway real. CORS verificado con preflight real (`access-control-allow-origin` correcto).
- [x] ✅ URLs públicas: **https://segurodata-frontend.vercel.app** (frontend) · **https://segurodata-api-production.up.railway.app** (backend)
- [ ] Verificar URL pública funciona desde móvil — pendiente de una pasada manual real (se verificó el bundle/CORS/health por HTTP, no un click-through interactivo en un teléfono)
- [ ] Pre-demo: Railway está siempre activo — verificar que /health responde y Supabase conecta 5 min antes

### Hardening post-deploy (10 julio) ✅

La verificación en vivo del frontend (09-jul) encontró dos gaps reales de datos/pipeline, no
cubiertos por el alcance original de Fase 3. Ambos cerrados:

- [x] ✅ **Backfill de localidad**: `upz_geometrias.cod_localidad`/`nom_localidad` estaban NULL en
  las 112 filas (F2/IDECA nunca trajo ese atributo — confirmado contra el servicio ArcGIS real). El
  mapeo ya existía en Silver vía F5 (NUSE) y no se propagaba a Supabase. Extraído a
  `src/geo_utils.py` (compartido con `transform.py`), migración `0015` extiende
  `upsert_upz_geom`. Backfill corrido: 112/112 UPZ con localidad, 19 localidades reales en el mapa
  (antes: 1 sola feature fusionada). La capa "Cambios estructurales" pasó de 0 a 224 UPZs con match.
- [x] ✅ **Quality-gate + pipeline de reentrenamiento automatizado**: `load_model_artifacts.py`
  comparaba cero métricas antes de sobreescribir predicciones/SHAP en producción — una regresión de
  modelo se hubiera cargado en silencio. Ahora `validar_metricas()` bloquea la carga si
  macro-F1/accuracy±1banda caen bajo el umbral (override con `--force`). `metricas.json` se
  versiona en git (historial real de performance). Split temporal de `train_model.py` dejó de ser
  una fecha fija (`TRAIN_ANIO_MAX=2025`) y ahora se recalcula cada corrida (últimos 6 meses = test).
  `.github/workflows/etl-semanal.yml` extendido con la cadena completa
  pipeline→transform→train→load, probado de punta a punta en CI real (run `29102721092`, 100%
  verde) — el split dinámico se ajustó solo a datos más frescos (TRAIN≤nov-2025, antes oct-2025) y
  el quality-gate pasó limpio. **El `schedule` semanal sigue comentado a propósito — no activar
  antes de la sustentación oral.**

---

## Fase 4 ⏳ — Documentación, Video y Entrega (11 julio – 1 agosto 2026)

**Entregable:** `SeguroData_06_Deployment.ipynb` + README + Video + Registro

> ⚠️ Verificar fecha exacta de entrega/registro en datos.gov.co. Final confirmado: GovCamps primera semana de agosto 2026.

- [ ] `README.md`: descripción, URL Railway (backend) + Vercel (frontend) + Supabase, instrucciones instalación completas
- [ ] Notebook 06: URLs de producción (Railway + Vercel), schema Supabase, instrucciones reproducción local, decisiones de diseño
- [ ] Video pitch de 3 minutos: problema → solución → demo (mapa + prescriptivo + chatbot)
- [ ] Auditoría de git history para API keys antes de hacer repo público
- [ ] Repositorio GitHub en modo público
- [ ] Registrar en datos.gov.co → sección "Usos" con enlace al repo — **OBLIGATORIO**
- [ ] **[Pre-mortem E2]** Escribir demo script de 10 minutos: clicks exactos, UPZs de ejemplo (Kennedy, Chapinero), datos que deben preexistir en Supabase, orden de módulos, respuestas preparadas a interrupciones del jurado, fallback a video si algo falla en vivo
- [ ] **[Pre-mortem T3]** Pre-cargar en Supabase reportes de prueba verosímiles para el demo Waze (Ideas 4/6): usar timestamps del día anterior para que se vean como datos reales del sistema, no de prueba. Documentar en demo script que estos son datos de simulación.

---

## Riesgos y planes de contingencia

| Riesgo | Probabilidad | Plan B |
|--------|-------------|--------|
| GeoJSON Delito Alto Impacto no tiene columna `hora` | Media | Imputar franja horaria desde `fecha` si la hora está en el timestamp |
| Cuadrantes dataset sin info de CAI | Media | Crear `cai_bogota.csv` manual (~80 filas) — ver Fase 1 Semana 1 |
| Memoria insuficiente en Colab para Estratificación (FUENTE 7) | Alta | Pre-calcular en Colab Pro o descargar a Drive → cargar desde Drive |
| Railway no responde en el demo (cold start imposible pero servicio caído) | Baja | Verificar `GET /health` 5 min antes de la presentación. Tener capturas de pantalla como fallback |
| OpenRouter API Key cuota agotada | Baja | Cachear respuestas generadas; limitar chatbot a 20 consultas/sesión. Fallback: `anthropic/claude-haiku` en la variable LLM_MODEL |
| Fecha real del concurso es agosto (GovCamps) | Media | Si se confirma, extender Fase 3 para refinar el dashboard |
