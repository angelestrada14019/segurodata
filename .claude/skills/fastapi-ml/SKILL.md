---
name: fastapi-ml
description: Backend FastAPI del sistema SeguroData — endpoints /predict, /explain, /graphrag, /prescribe en Google Cloud Run.
---

# FastAPI ML — SeguroData Bogotá

El backend Python es el único servicio de la Capa 4. Corre en Google Cloud Run (serverless, cold start 2-3s).

## Estructura del backend

```
backend/
├── main.py                  ← FastAPI app, CORS, middleware auth
├── routers/
│   ├── predict.py           ← POST /predict (XGBoost)
│   ├── explain.py           ← GET /explain (SHAP pre-computados)
│   ├── graphrag.py          ← POST /graphrag (pgvector + OpenRouter)
│   └── prescribe.py         ← POST /prescribe (tabla ontológica + OpenRouter)
└── requirements.txt
```

## Endpoints principales

```python
# POST /predict — inferencia XGBoost
{
  "upz_cod": "044",
  "mes": 7,
  "anio": 2026
}
# Response: { "nivel_riesgo": "ALTO", "probabilidades": {"ALTO": 0.82, "MEDIO": 0.15, "BAJO": 0.03} }

# GET /explain?upz_cod=044&mes=7&anio=2026 — SHAP desde Supabase (pre-computado)
# Response: { "shap_values": {"cuadrantes_por_km2": -0.34, "estrato_promedio_upz": 0.21, ...} }

# POST /graphrag — RAG sobre corpus F9/F10
{
  "pregunta": "¿Por qué aumentó el hurto en Kennedy en octubre 2023?",
  "upz_contexto": "044"
}
# Response: { "respuesta": "...", "fuentes": ["Boletín SCJ nov-2023", "El Tiempo 15-oct-2023"] }

# POST /prescribe — recomendación operacional
{
  "upz_cod": "044",
  "shap_top": [{"feature": "cuadrantes_por_km2", "valor": -0.34}, ...]
}
# Response: { "recomendacion": "UPZ 44 — Américas...", "entidades": ["MEBOG", "IDU"] }
```

## Variables de entorno (Cloud Run)

```bash
OPENROUTER_API_KEY=sk-or-...       # OpenRouter — gratis hasta 1M tokens/día
LLM_MODEL=google/gemini-flash-1.5  # Modelo por defecto (gratis)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...        # Service key — NUNCA exponer al frontend
```

## Desarrollo local

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs en: http://localhost:8000/docs
```

## Deploy a Google Cloud Run

```bash
gcloud run deploy segurodata-api \
  --source ./backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENROUTER_API_KEY=sk-or-...,LLM_MODEL=google/gemini-flash-1.5,SUPABASE_URL=...
```

## Pre-calentamiento del contenedor (demo)

Cloud Run escala a cero. Antes del demo en vivo:
```bash
# Visitar la URL 2 minutos antes para calentar el contenedor
curl https://segurodata-api-xxx-uc.a.run.app/health
```

## Integración con Supabase pgvector (GraphRAG)

```python
# El endpoint /graphrag usa sentence-transformers para embed la pregunta
# (all-MiniLM-L6-v2 — 384 dims, corre local en el contenedor)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode(pregunta).tolist()

# Luego busca en Supabase por similaridad coseno
result = supabase.rpc("match_documents", {
    "query_embedding": embedding,
    "match_threshold": 0.7,
    "match_count": 5,
    "filter_upz": upz_contexto
}).execute()
```

## Notas críticas

- La `OPENROUTER_API_KEY` se configura en Cloud Run — **NUNCA** en el frontend ni en el código
- SHAP values se cargan desde Supabase (pre-computados en Notebook 04) — NUNCA calcular on-demand
- El modelo XGBoost se serializa en `datos/modelos/xgboost_segurodata.joblib` y se carga al iniciar el backend
- CORS: permitir solo el dominio de Vercel en producción, localhost en desarrollo
