# SeguroData API — Backend FastAPI

Backend del sistema de predicción y prescripción de seguridad ciudadana por UPZ (Bogotá D.C.).
Corre en **Railway** (siempre activo). Datos y auth en **Supabase** (proyecto `segurodata`,
ref `pluxaelenhkdaakxdrpm`). LLM vía **OpenRouter** (server-side, la key nunca llega al browser).

> Contrato completo (schemas JSON, matriz endpoint×rol, decisiones D1-D12):
> `.claude/skills/backend-segurodata/SKILL.md`

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | — | Healthcheck (Railway) |
| GET | `/whoami` | JWT | Rol + cuadrante; `cuadrante_pendiente` (pre-mortem T5) |
| POST | `/predict` | JWT | Nivel de riesgo UPZ×mes (lookup a `predicciones` — nunca inferencia) |
| GET | `/explain` | JWT | SHAP top-3 pre-computado (completo para ANALISTA/ADMIN) |
| POST | `/graphrag` | JWT | Chatbot causal: pgvector + OpenRouter con citas (10/min) |
| POST | `/prescribe` | JWT (COMANDANTE+) | Tabla ontológica → entidad → acción + CAI + redacción LLM (10/min) |

Arquitectura en capas: `routers → services → repositories → clients`. El filtro por
rol/cuadrante vive en **services** (la service key bypasea RLS — regla D8).

## Desarrollo local

```bash
cd backend
pip install -r requirements-dev.txt   # liviano: fastembed en vez de torch
pip install fastapi "uvicorn[standard]" pydantic-settings supabase PyJWT structlog slowapi cachetools python-dotenv
cp .env.example .env                  # completar credenciales (ver abajo)
uvicorn app.main:app --reload         # docs: http://localhost:8000/docs
```

En `.env` local usa `EMBEDDINGS_BACKEND=fastembed` (mismo modelo MiniLM vía ONNX, sin torch)
y `AUTH_MODE=disabled` (inyecta usuario dev ADMIN — solo funciona con `ENV=development`).

### Tests

```bash
python -m pytest tests/ -q                       # suite unit (sin red), pre-mortems T5 incluido
python -m pytest tests/test_jwt_e2e.py -m integration -v   # E3: JWT end-to-end (requiere credenciales)
ruff check . && ruff format --check .
```

## ⚠️ Pasos manuales pendientes (Dashboard de Supabase)

1. **Credenciales en `backend/.env`** — Dashboard → Settings → API:
   - `SUPABASE_SERVICE_KEY` = service_role key (hoy el `.env` tiene la anon key como
     placeholder: el backend conecta pero RLS le bloquea las tablas → /predict devuelve 404).
   - `SUPABASE_JWT_SECRET` = JWT Secret (para verificar tokens de usuarios reales).
2. **Habilitar el hook de claims** — Dashboard → Authentication → Hooks → Custom Access Token
   → seleccionar `public.custom_access_token_hook`. Sin esto los tokens no traen `rol` ni
   `cuadrante_asignado` (el backend degrada con fallback a `user_profiles`, pero el RLS del
   frontend sí depende del claim).
3. *(Opcional)* `SUPABASE_DB_URL` (Dashboard → Connect → Session pooler) para:
   - `python scripts/seed_supabase.py` — geometrías reales F2/F4 + Silver completo (111K filas)
   - `python scripts/index_corpus.py --seed-demo` — reindexar corpus GraphRAG
4. *(Opcional)* `OPENROUTER_API_KEY` — sin ella, /graphrag y /prescribe degradan a texto
   determinista (útil en dev, insuficiente para el demo).

## Deploy a Railway (Fase 4 del cronograma — NO desplegado aún)

1. railway.app → New Project → Deploy from GitHub → **Root Directory: `backend/`**
   (detecta `Dockerfile` y `railway.toml` automáticamente).
2. Variables en el dashboard de Railway: las mismas de `.env.example` con `ENV=production`,
   `AUTH_MODE=enabled`, `EMBEDDINGS_BACKEND=sentence-transformers` y
   `CORS_ORIGINS=https://<dominio-vercel>`.
3. El healthcheck `/health` valida cada deploy (timeout 300s: la primera carga del modelo tarda).
4. Smoke test remoto: `/health` → `/predict` → `/graphrag` (<2s).

## Datos seed vs. reales

Las filas sintéticas llevan `origen='seed_dev'`. Cuando el Notebook 04 genere los artefactos
reales (`datos/modelos/predicciones.parquet` + `shap_values.parquet`):

```bash
python scripts/load_model_artifacts.py --dry-run   # valida esquemas
python scripts/load_model_artifacts.py             # borra seed_dev, carga notebook_04
```

El backend no cambia: sigue siendo lookup por PK.
