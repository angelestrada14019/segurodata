---
name: cloud-deploy-python
description: Deploy completo de SeguroData — FastAPI a Google Cloud Run + React a Vercel + setup Supabase.
---

# Cloud Deploy Python — SeguroData Bogotá

Deploy del sistema completo: backend Python (FastAPI → Cloud Run) + frontend React (→ Vercel) + base de datos (Supabase).

## Arquitectura de deploy

```
Frontend React + deck.gl  →  Vercel  (CDN global, siempre activo, gratis)
Backend FastAPI (Python)  →  Google Cloud Run  (serverless, cold start 2-3s, gratis 2M req/mes)
Base de datos             →  Supabase  (PostgreSQL + PostGIS + pgvector, siempre activo, gratis)
LLM proxy                 →  OpenRouter  (server-side en Cloud Run, NUNCA en browser)
```

## 1. Deploy Backend — Google Cloud Run

```bash
# Requisito: gcloud CLI instalado y configurado
gcloud auth login
gcloud config set project <tu-proyecto-gcp>

# Deploy desde el directorio del backend
gcloud run deploy segurodata-api \
  --source ./backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 60 \
  --set-env-vars \
    OPENROUTER_API_KEY=sk-or-...,\
    LLM_MODEL=google/gemini-flash-1.5,\
    SUPABASE_URL=https://xxx.supabase.co,\
    SUPABASE_SERVICE_KEY=eyJ...

# URL resultante: https://segurodata-api-xxx-uc.a.run.app
# Guardar esta URL para el frontend como VITE_API_URL
```

## 2. Deploy Frontend — Vercel

```bash
# Opción A: CLI de Vercel
cd frontend
vercel --cwd frontend
# Seleccionar framework: Vite
# Configurar variables de entorno cuando lo pida

# Opción B: desde vercel.com (recomendado)
# 1. Conectar repositorio GitHub en vercel.com
# 2. Seleccionar carpeta /frontend
# 3. Framework preset: Vite
# 4. Agregar variables de entorno
```

Variables de entorno en Vercel:
```
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...           (clave pública — OK exponer)
VITE_API_URL=https://segurodata-api-xxx-uc.a.run.app
```

## 3. Setup Supabase

```bash
# Desde la raíz del proyecto, con los datos generados por los notebooks:
python scripts/setup_supabase.py    # crea tablas + índices + extensiones
python scripts/load_silver.py       # carga silver_upz_mes.parquet (111,606 filas)
python scripts/load_predictions.py  # carga predicciones XGBoost pre-computadas
python scripts/load_shap.py         # carga SHAP values pre-computados (Notebook 04)
python scripts/load_geometrias.py   # carga 112 polígonos UPZ en PostGIS
python scripts/index_corpus.py      # genera embeddings F9/F10 → pgvector
```

Variables de entorno para los scripts:
```bash
# .env en raíz del proyecto
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...         (service key — NUNCA exponer al browser)
```

## Pre-calentamiento para el demo

Cloud Run escala a cero cuando no hay tráfico. Antes del demo:
```bash
# 2 minutos antes de la presentación, visitar la URL para calentar:
curl https://segurodata-api-xxx-uc.a.run.app/health
# El cold start tarda 2-3 segundos — solo ocurre si no hubo tráfico reciente
```

## Checklist de entrega (agosto 2026)

- [ ] FastAPI en Cloud Run respondiendo — URL pública activa
- [ ] React en Vercel — URL pública, los 4 módulos funcionando
- [ ] Supabase — Silver table + predicciones + SHAP + pgvector cargados
- [ ] Registro del proyecto en datos.gov.co (sección "Usos") — **OBLIGATORIO**
- [ ] README actualizado con las 3 URLs (GitHub + Vercel + Cloud Run)

## Costos del stack (demo/concurso)

| Servicio | Costo | Límite gratuito |
|---------|-------|----------------|
| Google Cloud Run | $0 | 2M requests/mes + 400K GB-segundos |
| Vercel | $0 | Bandwidth ilimitado en proyectos hobby |
| Supabase | $0 | 500 MB DB + 1 GB storage + 2 GB transfer |
| OpenRouter | $0 | Gemini Flash: 1M tokens/día gratis |
| **Total** | **$0** | Más que suficiente para el concurso |
