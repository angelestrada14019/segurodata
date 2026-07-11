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
python src/transform.py          # Bronze → Silver (111,606 × 20 cols)
python src/pipeline.py --status  # ver estado de cada fuente
```

⚠️ **F7 (estratificación, ~44K polígonos):** puede agotar RAM en Colab gratuito. Ver [[Transformacion]] para opciones.

---

## 2. Base de datos — Supabase

El proyecto Supabase ya está creado (`pluxaelenhkdaakxdrpm`). Las migraciones están en `supabase/migrations/` y ya fueron aplicadas. Para replicar desde cero:

### 2a. Aplicar migraciones (si partes de un proyecto nuevo)

Aplicar las 11 migraciones en orden desde el MCP Supabase o desde el SQL Editor del Dashboard:

```
supabase/migrations/
  20260610_0001_extensions.sql          ← postgis + vector
  20260610_0002_core_tables.sql         ← silver, predicciones, shap, change_points
  20260610_0003_geo_tables.sql          ← upz_geometrias, cuadrantes_geom (GIST)
  20260610_0004_documents_corpus.sql    ← pgvector HNSW 384 dims + RPC match_documents
  20260610_0005_auth_profiles.sql       ← user_profiles + trigger autoprovision
  20260610_0006_rls_policies.sql        ← RLS por rol
  20260610_0007_cuadrantes_telefono.sql ← nom_cai + teléfono
  20260610_0008_advisor_fixes.sql       ← índices + constraints
  20260611_0009_realtime.sql            ← Supabase Realtime (silver_upz_mes)
  20260611_0010_seed_rpc.sql            ← RPC match_documents (pgvector cosine)
  20260611_0011_predictions_metadata.sql← metadata JSONB (trazabilidad FTI)
```

### 2b. Cargar datos de producción en Supabase

> **Decisión FTI (11-jun-2026): Silver 111K queda LOCAL.** Supabase solo recibe outputs del modelo y datos geográficos, no datos de entrenamiento.

Requiere `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` en `backend/.env`:

```bash
# Geometrías UPZ/cuadrantes para el frontend
python scripts/seed_supabase.py --solo geo      # 112 UPZ + 599 cuadrantes via PostGIS

# Change points (ruptures PELT sobre F1 DAI 2018-2026)
python scripts/compute_change_points.py --pen 5 --max-bp 2  # 40 breakpoints → Supabase change_points

# Entrenar modelo XGBoost + pre-computar SHAP (NB03+NB04 equivalente)
python scripts/train_model.py                   # Gold → XGBoost → SHAP (exact 0.871 · ±1 banda 100% · macro-F1 0.867)

# Cargar predicciones + SHAP reales en Supabase (reemplaza seed_dev)
python scripts/load_model_artifacts.py          # 1,918 predicciones + 34,524 SHAP (origen='notebook_04')

# NO usar --solo silver: Silver permanece local para entrenamiento (patrón FTI)
```

### 2c. Paso manual obligatorio — custom_access_token_hook

Para que los roles (COMANDANTE_CAI, ANALISTA_SDSCJ, etc.) viajen en el JWT:

1. Supabase Dashboard → proyecto `segurodata`
2. Menú lateral: **Authentication → Auth Hooks**
3. Botón **"Add hook"** → seleccionar **"Customize Access Token (JWT) Claims hook"**
4. Tipo: **PostgreSQL Function** → schema: `public` → función: `custom_access_token_hook` → **Save**
5. Verificar que aparece **ENABLED** (verde)

> ✅ Estado actual (30-jun-2026): hook habilitado y activo.
> La función ya existe en la base de datos (migración `0005`).

Sin este paso todos los usuarios caen a rol `CIUDADANO`.

### 2d. Artefactos reales — ya cargados (16-jun-2026)

El modelo XGBoost fue entrenado con `scripts/train_model.py` y los artefactos reales cargados en Supabase. No se requiere seed sintético. Para re-entrenar y recargar:

```bash
python scripts/train_model.py           # regenera Gold + pkl + parquets
python scripts/load_model_artifacts.py  # sube a Supabase (origen='notebook_04')
```

---

## 3. Corpus GraphRAG — indexar F10

Los embeddings del corpus se generan con `fastembed` (`all-MiniLM-L6-v2`, 384 dims, local, sin costo de API) y se cargan en Supabase pgvector.

```bash
# Paso 1: descargar corpus F10 RSS
python src/pipeline.py --source f10

# Paso 2: indexar → chunks 500 tokens → MiniLM → pgvector
python scripts/index_corpus.py --seed-demo --backend fastembed   # demo + F10 real
python scripts/index_corpus.py --backend fastembed                # solo F10 real

# Sin credenciales (genera SQL para importar manualmente):
python scripts/index_corpus.py --seed-demo --emit-sql  # genera datos/grafo/corpus_seed.sql
```

> **Estado actual (30-jun-2026):** 10 chunks RSS reales en Supabase (El Tiempo + El Informante; SEED_DEV eliminados). `/graphrag` responde con fuentes reales.

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

### Deploy en Railway — ✅ desplegado

**https://segurodata-api-production.up.railway.app** — `GET /health` responde 200.

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
VITE_API_URL=https://segurodata-api-production.up.railway.app
```

### Deploy en Vercel — ✅ desplegado

```bash
cd frontend
vercel link --project segurodata-frontend
vercel env add VITE_SUPABASE_URL production --value "..."
vercel env add VITE_SUPABASE_ANON_KEY production --value "..."
vercel env add VITE_API_URL production --value "https://segurodata-api-production.up.railway.app"
vercel --prod
```

> **Estado actual:** **https://segurodata-frontend.vercel.app** — 4 módulos + modal de 5 pestañas +
> Panel Admin en producción, apuntando al backend real de Railway. CORS verificado.

---

## 6. GitHub Actions — pipeline de reentrenamiento (opcional, ya probado en CI real)

`.github/workflows/etl-semanal.yml` corre la cadena completa (descarga → Silver → reentrena →
quality-gate → carga a Supabase) bajo demanda. El `schedule` semanal queda **desactivado a
propósito** — no lo actives antes de la sustentación oral.

**1. Configurar secrets** (GitHub → repo → Settings → Secrets and variables → Actions → New
repository secret):

| Secret | Valor |
|---|---|
| `SUPABASE_URL` | mismo valor que `backend/.env` |
| `SUPABASE_SERVICE_KEY` | mismo valor que `backend/.env` (service key, nunca la anon) |
| `SOCRATA_APP_TOKEN` | opcional — solo afecta la descarga de F6 (Hurto PN), que no alimenta el modelo |

**2. Habilitar permiso de escritura** (GitHub → repo → Settings → Actions → General → Workflow
permissions): marcar **"Read and write permissions"** y guardar. Sin esto, el paso final (commit
de `metricas.json` de vuelta al repo) falla con 403 — el `GITHUB_TOKEN` automático es de solo
lectura por defecto.

**3. Disparar manualmente**: GitHub → Actions → "Pipeline de datos y reentrenamiento" → "Run
workflow". El input `retrain` (default `true`) controla si corre solo el ETL de datos crudos
(`false`) o la cadena completa incluyendo reentrenamiento (`true`).

```bash
gh workflow run etl-semanal.yml   # o desde la UI de GitHub Actions
```

---

## Variables de entorno — resumen

> **Claves Supabase — dos formatos válidos hasta fin 2026:**
> - Nuevo: `sb_publishable_...` (frontend) / `sb_secret_...` (backend)
> - Legacy JWT: clave `anon` (frontend) / `service_role` (backend)
> Ambos funcionan igual. El nuevo formato tiene protección extra contra uso en browser.

| Variable | Componente | Dónde obtener |
|----------|-----------|---------------|
| `SUPABASE_URL` | Backend + scripts + GitHub Actions | Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Backend + scripts + GitHub Actions | Dashboard → API → **Secret key** (nuevo) o service_role JWT (legacy) |
| `SOCRATA_APP_TOKEN` | Pipeline F6 (opcional) + GitHub Actions | dev.socrata.com → registrar app |
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
