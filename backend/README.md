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
| PATCH | `/admin/usuarios/{user_id}/cuadrante` | JWT (ADMIN) | Asigna cuadrante a un comandante sin cuadrante asignado |

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

## Setup local desde cero (Dashboard de Supabase)

Si estás replicando el proyecto o configurando un `.env` local nuevo:

1. **Credenciales en `backend/.env`** — Dashboard → Settings → API:
   - `SUPABASE_SERVICE_KEY` = service_role key (con la anon key como placeholder, el backend
     conecta pero RLS bloquea las tablas → `/predict` devuelve 404).
   - `SUPABASE_JWT_SECRET` — no se usa para verificar tokens: el proyecto firma con **ES256/JWKS**,
     no HS256, así que la verificación real usa `SUPABASE_JWKS_URL` (ver `app/config.py`).
2. **Hook de claims** — Dashboard → Authentication → Hooks → Custom Access Token
   → seleccionar `public.custom_access_token_hook`. Sin esto los tokens no traen `rol` ni
   `cuadrante_asignado` (el backend degrada con fallback a `user_profiles`, pero el RLS del
   frontend sí depende del claim).
3. `SUPABASE_DB_URL` (Dashboard → Connect → Session pooler) para:
   - `python scripts/seed_supabase.py` — geometrías reales F2/F4 + Silver completo
   - `python scripts/index_corpus.py` — reindexar corpus GraphRAG
4. `OPENROUTER_API_KEY` — sin ella, `/graphrag` y `/prescribe` degradan a texto
   determinista (útil en dev, insuficiente para el demo).

## Deploy a Railway — EN PRODUCCIÓN

Proyecto `segurodata-api`, desplegado vía CLI (`railway up` desde `./backend`).

- **URL pública**: https://segurodata-api-production.up.railway.app
- **Docs**: https://segurodata-api-production.up.railway.app/docs
- **Healthcheck**: `GET /health` → `{"status":"ok","env":"production"}` (Railway lo valida en
  cada deploy, timeout 300s porque la primera carga del modelo de embeddings tarda).
- Variables configuradas en el dashboard de Railway: `ENV=production`, `AUTH_MODE=enabled`,
  `EMBEDDINGS_BACKEND=sentence-transformers`, `CORS_ORIGINS` apuntando al dominio real de Vercel
  (el `.env.example`/código por defecto trae `localhost` solo para desarrollo — la producción
  usa el override del dashboard, verificado con preflight CORS real).

Para redesplegar tras un cambio: `cd backend && railway up`.

## Datos seed vs. reales

`origen='seed_dev'` ya no existe en producción — fue reemplazado por completo con los artefactos
reales de `scripts/train_model.py` (predicciones + SHAP con `origen='notebook_04'`). Para
recargar tras un reentrenamiento:

```bash
python scripts/load_model_artifacts.py --dry-run   # valida esquemas y compara métricas (quality-gate)
python scripts/load_model_artifacts.py             # sube el modelo nuevo (bloquea si es peor que el actual)
python scripts/load_model_artifacts.py --force      # sobreescribe aunque las métricas empeoren
```

El backend no cambia: sigue siendo lookup por PK, nunca inferencia on-demand.
