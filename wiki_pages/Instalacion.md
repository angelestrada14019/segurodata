# Guía de Instalación

El proyecto tiene tres componentes: **pipeline de datos** (Python), **backend ML** (FastAPI → Railway), y **frontend** (React → Vercel). Base de datos: Supabase (PostgreSQL + PostGIS + pgvector). Proyecto Supabase: `segurodata` (ref `pluxaelenhkdaakxdrpm`, us-east-1).

---

## 1. Pipeline de datos (Python) — notebooks + ETL

```bash
git clone https://github.com/angelestrada14019/segurodata.git
cd segurodata

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Descargar Bronze y generar Silver
python src/pipeline.py           # descarga 12 fuentes (incremental)
python src/transform.py          # Bronze → Silver (111,606 × 23 cols)
python src/pipeline.py --status  # ver estado de cada fuente
```

⚠️ **F7 (estratificación, ~44K polígonos):** puede agotar RAM en Colab gratuito. Ver [[Transformacion]] para opciones.

---

## 2. Base de datos — Supabase

El proyecto Supabase ya está creado (`pluxaelenhkdaakxdrpm`). Las migraciones están en `supabase/migrations/` y ya fueron aplicadas. Para replicar desde cero:

### 2a. Aplicar migraciones (si partes de un proyecto nuevo)

Aplicar las 8 migraciones en orden desde el MCP Supabase o desde el SQL Editor del Dashboard:

```
supabase/migrations/
  20260610_0001_extensions.sql      ← postgis + vector
  20260610_0002_core_tables.sql     ← silver, predicciones, shap, change_points
  20260610_0003_geo_tables.sql      ← upz_geometrias, cuadrantes_geom (GIST)
  20260610_0004_documents_corpus.sql← pgvector HNSW 384 dims + RPC match_documents
  20260610_0005_auth_profiles.sql   ← user_profiles + trigger autoprovision
  20260610_0006_rls_policies.sql    ← RLS por rol
  20260610_0007_cuadrantes_telefono.sql
  20260610_0008_advisor_fixes.sql
```

### 2b. Cargar datos (seed + Silver)

Requiere `SUPABASE_DB_URL` en `backend/.env` (Settings → Database → Session pooler):

```bash
# Todo: Silver 111K + geometrías F2/F4 + predicciones y SHAP sintéticos
python scripts/seed_supabase.py

# O por partes:
python scripts/seed_supabase.py --solo silver   # 111,606 filas vía COPY
python scripts/seed_supabase.py --solo geo      # 112 UPZ + 599 cuadrantes
python scripts/seed_supabase.py --solo synth    # predicciones y SHAP seed_dev
```

### 2c. Paso manual obligatorio — custom_access_token_hook

Para que los roles (COMANDANTE_CAI, ANALISTA_SDSCJ, etc.) viajen en el JWT:

1. Supabase Dashboard → proyecto `segurodata`
2. Menú lateral: **Authentication → Hooks**
3. Sección "Custom Access Token" → tipo **PostgreSQL Function**
4. Seleccionar `public.custom_access_token_hook` → **Save**

> La función ya existe en la base de datos (migración `0005`). Solo hay que habilitarla aquí.

Sin este paso todos los usuarios caen a rol `CIUDADANO`.

### 2d. Switch a artefactos reales (post Notebook 04)

```bash
python scripts/load_model_artifacts.py \
  --predicciones datos/modelos/predicciones_xgboost.parquet \
  --shap datos/modelos/shap_values.parquet
# Reemplaza origen='seed_dev' → 'notebook_04' sin tocar código
```

---

## 3. Corpus GraphRAG — indexar F9 + F10

Los embeddings del corpus (boletines SCJ + noticias) se generan con `sentence-transformers all-MiniLM-L6-v2` (local, sin costo de API) y se cargan en Supabase pgvector.

```bash
# Paso 1: descargar corpus (si no existe en datos/raw/)
python src/pipeline.py --source f9 f10

# Paso 2: indexar → chunks 500 tokens → MiniLM → pgvector
python scripts/index_corpus.py

# Para demo sin F9/F10 reales (10 chunks SEED_DEV ya cargados en Supabase):
python scripts/index_corpus.py --seed-demo          # carga directo a DB
python scripts/index_corpus.py --seed-demo --emit-sql  # genera datos/grafo/corpus_seed.sql
```

> **Estado actual (10-jun-2026):** 10 chunks demo (`SEED_DEV`) cargados → `/graphrag` es demostrable. F9/F10 reales pendientes.

---

## 4. Backend ML — FastAPI

### Desarrollo local

```bash
cd backend
pip install -r requirements.txt

# Copiar y rellenar credenciales
cp .env.example .env
# Editar backend/.env — variables mínimas:
#   SUPABASE_URL=https://pluxaelenhkdaakxdrpm.supabase.co
#   SUPABASE_SERVICE_KEY=<sb_secret_... o legacy service_role JWT>
#   SUPABASE_JWT_SECRET=   # dejar vacío si el proyecto usa ES256 (ver SUPABASE_JWKS_URL)
#   SUPABASE_JWKS_URL=https://<ref>.supabase.co/auth/v1/.well-known/jwks.json
#   OPENROUTER_API_KEY=<key de openrouter.ai>
#   AUTH_MODE=disabled  # solo en development

uvicorn app.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

### Verificación local

```bash
pytest tests/ -m "not integration" -v   # 31 tests — no requieren credenciales
ruff check .                             # lint
```

Ver skill `backend-testing` para la guía completa de verificación E2E.

### Deploy en Railway (Fase 4)

```bash
# Opción A — GitHub integration (recomendada):
# railway.app → New Project → Deploy from GitHub
# Root Directory: backend/   (Railway detecta el Dockerfile automáticamente)
# Configurar variables de entorno en el dashboard de Railway

# Opción B — CLI:
npm install -g @railway/cli
railway login
cd backend
railway link
railway up
```

Variables a configurar en Railway:

| Variable | Valor |
|----------|-------|
| `ENV` | `production` |
| `AUTH_MODE` | `enabled` |
| `SUPABASE_URL` | `https://pluxaelenhkdaakxdrpm.supabase.co` |
| `SUPABASE_SERVICE_KEY` | `sb_secret_...` (nuevo) o legacy service_role JWT |
| `SUPABASE_JWT_SECRET` | dejar vacío si el proyecto usa ES256 (JWKS) |
| `SUPABASE_JWKS_URL` | `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json` |
| `OPENROUTER_API_KEY` | key de openrouter.ai |
| `LLM_MODEL` | `google/gemini-flash-1.5` |

Railway (Plan Hobby ~$5/mes) mantiene el proceso siempre activo — sin cold start, sin warmup previo al demo.

---

## 5. Frontend — React + deck.gl (Fase 3)

```bash
cd frontend
npm install

# Desarrollo local
npm run dev       # http://localhost:5173

# Variables de entorno (frontend/.env.local):
VITE_SUPABASE_URL=https://pluxaelenhkdaakxdrpm.supabase.co
VITE_SUPABASE_ANON_KEY=<anon key pública>
VITE_API_URL=https://segurodata-api.up.railway.app
```

### Deploy en Vercel

```bash
vercel --cwd frontend
# O conectar repo en vercel.com → Root Directory: frontend/
```

> **Estado actual:** frontend pendiente — Fase 3 (21 jun – 10 jul 2026).

---

## Variables de entorno — resumen

> **Claves Supabase — dos formatos válidos hasta fin 2026:**
> - Nuevo: `sb_publishable_...` (frontend) / `sb_secret_...` (backend)
> - Legacy JWT: clave `anon` (frontend) / `service_role` (backend)
> Ambos funcionan igual. El nuevo formato tiene protección extra contra uso en browser.

| Variable | Componente | Dónde obtener |
|----------|-----------|---------------|
| `SUPABASE_URL` | Backend + scripts | Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Backend + scripts | Dashboard → API → **Secret key** (nuevo) o service_role JWT (legacy) |
| `SUPABASE_JWT_SECRET` | Backend — solo si HS256 legacy | Dashboard → Settings → API → JWT Secret (dejar vacío si usa ES256) |
| `SUPABASE_JWKS_URL` | Backend — si ES256/RS256 | `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` |
| `SUPABASE_DB_URL` | Scripts offline (seed COPY) | Dashboard → Settings → Database → Session pooler |
| `OPENROUTER_API_KEY` | Backend (LLM) | openrouter.ai → Keys |
| `LLM_MODEL` | Backend | `google/gemini-flash-1.5` (por defecto) |
| `AUTH_MODE` | Backend | `disabled` solo en development |
| `VITE_SUPABASE_URL` | Frontend build | Igual que SUPABASE_URL |
| `VITE_SUPABASE_ANON_KEY` | Frontend (lectura pública) | Dashboard → API → **Publishable key** (nuevo) o anon JWT (legacy) |
| `VITE_API_URL` | Frontend build | URL pública de Railway |

Open-Meteo, CKAN, Socrata y ArcGIS son APIs públicas sin autenticación.
