# Guía de Instalación

El proyecto tiene tres componentes: **pipeline de datos** (Python), **backend ML** (FastAPI/Python), y **frontend** (React). En producción corren en Railway (backend) + Vercel (frontend) + Supabase (BD).

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
#   ANTHROPIC_API_KEY=sk-ant-...       (Módulos 3 y 4)
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

## 2. Backend ML — FastAPI

```bash
cd backend
pip install -r requirements.txt    # fastapi, uvicorn, xgboost, shap, langchain-anthropic

# Desarrollo local
uvicorn main:app --reload --port 8000

# Variables de entorno requeridas
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...        # service role (no anon)
MODEL_PATH=../datos/modelos/xgboost_segurodata.pkl
```

### Deploy en Railway

```bash
# Desde raíz del repo
railway login
railway new
railway add --service backend
railway deploy
# Railway detecta automáticamente el Dockerfile o requirements.txt en /backend
```

---

## 3. Base de datos — Supabase

1. Crear proyecto en https://supabase.com/dashboard
2. Habilitar extensiones:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```
3. Ejecutar schema inicial:
```bash
# Desde raíz del repo
python scripts/setup_supabase.py   # crea tablas + índices + carga Silver
```
4. Cargar tabla Silver desde parquet:
```python
import polars as pl
from supabase import create_client

silver = pl.read_parquet("datos/procesados/silver_upz_mes.parquet")
# → subir a Supabase tabla silver_upz_mes
```

---

## 4. Frontend — React + deck.gl

```bash
cd frontend
npm install              # instala React, deck.gl, MapLibre, Tailwind, supabase-js

# Desarrollo local
npm run dev              # abre en http://localhost:5173

# Variables de entorno (.env.local)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_API_URL=http://localhost:8000   # o URL de Railway en producción
```

### Deploy en Vercel

```bash
# Desde raíz del repo
vercel --cwd frontend
# O conectar repo GitHub en vercel.com → seleccionar carpeta /frontend
```

---

## Variables de entorno — resumen

| Variable | Componente | Cómo obtener |
|----------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Backend + pipeline | console.anthropic.com |
| `SUPABASE_URL` | Backend + frontend + pipeline | Supabase Dashboard → Settings → API |
| `SUPABASE_ANON_KEY` | Frontend (lectura pública) | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Backend (escritura) | Supabase Dashboard → Settings → API |
| `VITE_API_URL` | Frontend | URL de Railway una vez desplegado |

Open-Meteo, CKAN, Socrata son APIs públicas sin autenticación requerida.
