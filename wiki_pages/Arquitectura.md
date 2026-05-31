# Arquitectura del Sistema

## Visión general — 5 capas

```
┌─────────────────────────────────────────────────────────────────────┐
│  CAPA 5 — FRONTEND                                                   │
│  React + Vite + deck.gl + Tailwind CSS  →  Vercel (CDN, siempre ON) │
│  4 páginas: Diagnóstico / Predicción / Prescriptivo / Chatbot       │
├─────────────────────────────────────────────────────────────────────┤
│  CAPA 4 — BACKEND SERVERLESS                                         │
│  [Demo]      Supabase Edge Functions (Deno) — siempre activo        │
│              graphrag() → pgvector search → OpenRouter → respuesta  │
│  [Producción] Google Cloud Run (FastAPI) — cold start 2-3s          │
│              /predict (XGBoost) · /explain (SHAP) · /query (RAG)   │
├───────────────────────────┬─────────────────────────────────────────┤
│  CAPA 3 — BASE DE DATOS   │  CAPA 3B — VECTOR STORE                 │
│  Supabase PostgreSQL       │  Supabase pgvector (384 dims)           │
│  + PostGIS (geometrías UPZ)│  Embeddings F9/F10 corpus               │
│  predictions (1,920 filas) │  sentence-transformers all-MiniLM-L6-v2│
│  shap_values pre-computados│  (indexado una sola vez, offline)       │
│  change_points (ruptures)  │                                         │
├───────────────────────────┴─────────────────────────────────────────┤
│  CAPA 2 — MODEL / GOLD                                               │
│  datos/modelos/  XGBoost + SHAP pre-computado + ruptures            │
│  datos/features/ tabla_maestra_upz.parquet (17 variables)           │
├─────────────────────────────────────────────────────────────────────┤
│  CAPA 1 — BRONZE / SILVER                                            │
│  Bronze: datos/raw/    ← src/pipeline.py   (12 fuentes F1-F14)      │
│  Silver: datos/procesados/ ← src/transform.py  (111,606 × 23 cols)  │
└─────────────────────────────────────────────────────────────────────┘
```

## Demo vs Producción — modos de deploy

| Componente | Demo concurso | Producción (post-concurso) |
|---|---|---|
| Frontend | Vercel (gratis, CDN) | Vercel (igual) |
| Predicciones XGBoost | Pre-computadas en Supabase | FastAPI en Google Cloud Run |
| GraphRAG / Chatbot | Supabase Edge Function → OpenRouter | Google Cloud Run FastAPI |
| LLM | OpenRouter: Gemini Flash (gratis) | OpenRouter: modelo configurable |
| Embeddings | Indexados offline con sentence-transformers | Igual (índice persistente) |
| Keep-alive | No necesario — todo serverless | No necesario — Cloud Run escala |
| Costo mensual | $0 | ~$0-5 (Cloud Run free tier + OpenRouter) |

## Medallion Architecture (datos)

```
Bronze  datos/raw/          src/pipeline.py   ← 12 fuentes, descarga incremental
Silver  datos/procesados/   src/transform.py  ← silver_upz_mes.parquet (111,606 × 23)
Gold    datos/features/     Notebook 03       ← 17 variables + tabla prescriptiva
Model   datos/modelos/      Notebook 04       ← XGBoost + SHAP pre-computado
```

## La tabla Silver (actualizada)

La tabla Silver tiene una fila por cada combinación **UPZ × mes × tipo de incidente** (86 tipos NUSE):

- **Genera filas**: F5 NUSE (128,314 registros raw → 111,606 filas silver)
- **Agrega columnas**: F3 (clima), F4 (cuadrantes), F7 (estrato), F8 (TransMilenio)
- **Nuevas columnas**: F11 (obras IDU), F13 (cámaras Salvavidas), F14 (alumbrado UAESP)
- **No entra al JOIN**: F1 (solo localidad), F6 (solo municipio)
- **Base geométrica**: F2 UPZ (spatial join)

**Resultado: 111,606 filas × 23 columnas, 120 UPZs, 86 tipos NUSE, 19 localidades**

## Stack de aplicación

### Frontend — React + deck.gl
```
React 18 + Vite + Tailwind CSS
deck.gl: PolygonLayer (UPZs coloreadas ALTO/MEDIO/BAJO)
         ScatterplotLayer (cámaras Salvavidas F13)
         HeatmapLayer (densidad de incidentes)
MapLibre GL JS: basemap OSM gratuito
supabase-js: acceso directo a PostgreSQL + Realtime desde React
```

### Backend — Supabase Edge Functions (demo) + Google Cloud Run (producción)

**Demo (Edge Functions — Deno/TypeScript):**
```typescript
// supabase/functions/graphrag/index.ts
// Recibe pregunta → busca pgvector → llama OpenRouter → devuelve respuesta
// OPENROUTER_API_KEY queda server-side (no expuesta al browser)
```

**Producción (Google Cloud Run — FastAPI Python):**
```python
# Endpoints principales
POST /predict   → XGBoost: {upz, fecha} → {nivel_riesgo, probabilidades}
GET  /explain   → SHAP: {upz, mes} → shap_values pre-computados desde Supabase
POST /query     → GraphRAG: {pregunta, upz_contexto} → OpenRouter response
```

### Base de datos — Supabase
```sql
-- Tablas principales
silver_upz_mes     -- 111,606 filas (importada desde Silver parquet)
shap_values        -- SHAP pre-computados por UPZ × mes (Notebook 04)
upz_geometrias     -- 112 polígonos PostGIS (EPSG:4326)
change_points      -- Puntos de cambio ruptures por localidad (2018-2026)

-- Extensiones habilitadas
CREATE EXTENSION postgis;
CREATE EXTENSION vector;  -- pgvector para embeddings GraphRAG
```

## GraphRAG — sentence-transformers + Supabase pgvector + OpenRouter

Los corpus de texto (F9 boletines SCJ + F10 noticias RSS + F12 Plan Desarrollo) se indexan como embeddings en Supabase pgvector:

```
INDEXACIÓN (offline, una sola vez — scripts/index_corpus.py):
F9 PDF  → pdfplumber → texto → sentence-transformers (all-MiniLM-L6-v2) → pgvector
F10 RSS → feedparser → texto → sentence-transformers (all-MiniLM-L6-v2) → pgvector
F12 PDF → pdfplumber → texto → sentence-transformers (all-MiniLM-L6-v2) → pgvector

CONSULTA EN TIEMPO REAL (Supabase Edge Function — Deno):
pregunta_usuario
    → sentence-transformers embed (o API de embeddings ligera)
    → Supabase match_documents RPC (pgvector cosine similarity)
    → chunks relevantes recuperados
    → OpenRouter API (google/gemini-flash-1.5)
    → respuesta operacional con citas de fuentes reales
```

**Por qué sentence-transformers:** corre local en Python sin costo de API. Genera 384 dimensiones compatibles con pgvector. Un modelo de 22MB que procesa 220 documentos en segundos.

**Por qué OpenRouter:** una sola API key da acceso a 200+ modelos. `google/gemini-flash-1.5` es gratuito (1M tokens/día) y multilingüe — ideal para el chatbot en español. Si se requiere mayor calidad, se cambia la variable `LLM_MODEL` sin tocar código.

## Detección de puntos de cambio (ruptures)

El módulo de change point detection corre sobre F1 DAI histórico (2018–2026) por localidad:

```python
import ruptures as rpt
# PELT: Pruned Exact Linear Time — detecta cambios en media/varianza de la serie
algo = rpt.Pelt(model="rbf").fit(serie_mensual_localidad)
breakpoints = algo.predict(pen=10)
```

Los resultados se guardan en Supabase tabla `change_points` y alimentan el Módulo 3 (Prescriptivo): si hay un cambio estructural reciente + tendencia sostenida → el diagnóstico es "problema estructural" (no pico temporal) → acción diferente.

## Diagrama de arquitectura

![Diagrama de arquitectura de fuentes SeguroData](diagrama_arquitectura.svg)
