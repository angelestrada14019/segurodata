# Guía de Instalación

El proyecto tiene tres componentes: **pipeline de datos** (Python), **backend ML** (FastAPI en Railway), y **frontend** (React). En producción: Vercel (frontend) + Supabase (BD + pgvector) + Railway (backend). Todo el backend es Python.

---

## 1. Pipeline de datos (Python) — notebooks + ETL

```bash
# Clonar el repositorio
git clone https://github.com/angelestrada14019/segurodata.git
cd segurodata

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# Instalar dependencias de datos
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env:
#   OPENROUTER_API_KEY=sk-or-...        (Módulos 3 y 4 — gratis en openrouter.ai)
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_ANON_KEY=eyJ...
```

### Descarga Bronze y generación Silver

```bash
python src/pipeline.py           # descarga 12 fuentes (solo lo nuevo)
python src/transform.py          # Bronze → Silver (111,606 × 23 cols)
python src/pipeline.py --status  # ver estado de cada fuente
```

### En Google Colab

```python
!git clone https://github.com/angelestrada14019/segurodata.git
%cd segurodata
!pip install -r requirements.txt -q
!python src/pipeline.py
!python src/transform.py
```

⚠️ **F7 (estratificación, ~44K polígonos):** puede agotar RAM en Colab gratuito. Ver [[Transformacion]] para opciones.

---

## 2. Indexar corpus GraphRAG (una sola vez)

Genera los embeddings del corpus de texto (F9 + F10) y los carga en Supabase pgvector:

```bash
# Requiere que F9/F10 Bronze existan (pipeline.py --source f9 f10)
python scripts/index_corpus.py
# Usa sentence-transformers all-MiniLM-L6-v2 (local, sin costo de API)
# Resultado: ~220 embeddings de 384 dims → Supabase pgvector tabla 'documents'
```

---

## 3. Base de datos — Supabase

1. Crear proyecto en https://supabase.com/dashboard
2. Habilitar extensiones:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```
3. Aplicar schema y cargar datos:
```bash
python scripts/setup_supabase.py   # crea tablas + índices
python scripts/load_silver.py      # carga silver_upz_mes.parquet
python scripts/load_predictions.py # carga predicciones XGBoost pre-computadas
python scripts/load_shap.py        # carga SHAP values pre-computados
python scripts/index_corpus.py     # carga embeddings pgvector
```

---

## 4. Backend ML — FastAPI (Railway)

El backend Python sirve el GraphRAG, el prescriptivo y la inferencia XGBoost. La `OPENROUTER_API_KEY` permanece en Railway — nunca en el browser. Railway mantiene el servicio siempre activo: sin cold start, sin warmup previo al demo.

### Desarrollo local
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Variables de entorno (.env en /backend):
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL=google/gemini-flash-1.5
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
```

### Deploy en Railway
```bash
# Instalar Railway CLI (una sola vez)
npm install -g @railway/cli

# Login y deploy
railway login
cd backend
railway link          # seleccionar proyecto en el dashboard de railway.app
railway up            # despliega desde ./backend

# Configurar variables de entorno en Railway dashboard o CLI:
railway variables set OPENROUTER_API_KEY=sk-or-...
railway variables set LLM_MODEL=google/gemini-flash-1.5
railway variables set SUPABASE_URL=https://xxx.supabase.co
railway variables set SUPABASE_SERVICE_KEY=eyJ...

# La URL pública queda disponible en Railway dashboard:
# VITE_API_URL=https://segurodata-api.up.railway.app
```

Railway (Plan Hobby ~$5/mes) mantiene el proceso activo permanentemente. **Pre-demo:** verificar que `GET /health` responde antes de la presentación. Sin warmup, sin cron adicional.

---

## 5. Frontend — React + deck.gl

```bash
cd frontend
npm install              # instala React, deck.gl, MapLibre, Tailwind, supabase-js

# Desarrollo local
npm run dev              # abre en http://localhost:5173

# Variables de entorno (.env.local)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

### Deploy en Vercel

```bash
vercel --cwd frontend
# O conectar repo GitHub en vercel.com → seleccionar carpeta /frontend
```

---

## Variables de entorno — resumen

| Variable | Componente | Cómo obtener |
|----------|-----------|-------------|
| `OPENROUTER_API_KEY` | Backend FastAPI (Railway) | openrouter.ai (gratis con límites) |
| `LLM_MODEL` | Backend FastAPI (Railway) | `google/gemini-flash-1.5` (por defecto, gratis) |
| `SUPABASE_URL` | Todos | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Frontend (lectura pública) | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Scripts de carga | Supabase Dashboard → Settings → API |
| `VITE_SUPABASE_URL` | Frontend build | Igual que SUPABASE_URL |

Open-Meteo, CKAN, Socrata son APIs públicas sin autenticación requerida.
