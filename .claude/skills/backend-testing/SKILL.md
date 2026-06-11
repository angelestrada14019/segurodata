---
name: backend-testing
description: Guía completa para verificar el backend SeguroData — qué credenciales configurar, qué pasos manuales hacer en Supabase Dashboard, y cómo correr cada nivel de pruebas (unit, integración E3, seed de datos, corpus).
---

# Backend Testing — SeguroData Bogotá

El backend tiene **dos niveles de prueba**: los tests unitarios no necesitan ninguna credencial (corren con fakes); los de integración requieren credenciales reales del proyecto Supabase `segurodata` (ref `pluxaelenhkdaakxdrpm`).

---

## Nivel 0 — Tests unitarios (sin credenciales, correr YA)

No requieren Supabase ni OpenRouter. Todos los repos y clientes están sustituidos por fakes en `backend/tests/conftest.py`.

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -m "not integration" -v
ruff check .
```

**Resultado esperado:** 31 passed, 0 failed · ruff: All checks passed

---

## Nivel 1 — Configurar credenciales reales

Antes de cualquier prueba con datos reales, rellenar `backend/.env` a partir de `.env.example`.

### Dónde encontrar cada valor

| Variable | Ruta en Supabase Dashboard |
|----------|---------------------------|
| `SUPABASE_URL` | Ya está: `https://pluxaelenhkdaakxdrpm.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Settings → API → **service_role** (⚠️ nunca al frontend) |
| `SUPABASE_JWT_SECRET` | Settings → API → **JWT Secret** (sección "JWT Settings") |
| `SUPABASE_DB_URL` | Settings → Database → **Connection string** → Session pooler (modo `?sslmode=require`) |
| `SUPABASE_JWKS_URL` | Dejar vacío — el proyecto usa HS256 legacy, no necesita JWKS |
| `OPENROUTER_API_KEY` | openrouter.ai → Keys → Create key |
| `LLM_MODEL` | Por defecto `google/gemini-flash-1.5` (gratuito, no cambiar) |

**Configuración mínima para integración básica** (sin LLM):
```env
ENV=development
AUTH_MODE=disabled
SUPABASE_URL=https://pluxaelenhkdaakxdrpm.supabase.co
SUPABASE_SERVICE_KEY=<pegar aquí>
SUPABASE_JWT_SECRET=<pegar aquí>
```

---

## Nivel 2 — Paso manual en Supabase Dashboard (UNA SOLA VEZ)

El **custom_access_token_hook** inyecta los claims `rol` y `cuadrante_asignado` en el JWT. Sin este paso, los usuarios no tienen rol en el token y caen todos a `CIUDADANO`.

### Cómo habilitarlo:

1. Ir a [supabase.com/dashboard](https://supabase.com/dashboard) → proyecto `segurodata`
2. Menú lateral → **Authentication** → **Hooks**
3. Buscar **"Custom Access Token Hook"** (o "JWT Hook")
4. Seleccionar la función `custom_access_token_hook` (creada en migración 0005)
5. Activar el toggle → **Save**
6. Verificar: crear usuario de prueba y revisar que el JWT incluye `"rol": "CIUDADANO"` o el rol correspondiente

> **Por qué esto no se puede automatizar:** el Dashboard de Supabase no expone esta configuración por API/MCP — es un click manual obligatorio.

---

## Nivel 3 — Pre-mortem E3 (test JWT real contra Supabase)

Verifica que FastAPI decodifica correctamente tokens reales de Supabase Auth.

```bash
cd backend
# Requiere SUPABASE_URL + SUPABASE_JWT_SECRET + SUPABASE_SERVICE_KEY en .env
pytest tests/test_jwt_e2e.py -m integration -v
```

**Qué testea `test_jwt_e2e.py`:**
1. Crear usuario de prueba vía Supabase Admin API
2. Obtener JWT real de Supabase Auth
3. Llamar `POST /predict` con `Authorization: Bearer {token_real}`
4. Verificar que FastAPI lo decodifica y extrae `rol` correctamente
5. Limpiar el usuario de prueba

**Evidencia esperada:** 1 passed — desbloquea Fase 3 del CRONOGRAMA.

---

## Nivel 4 — Cargar datos reales en Supabase

### 4a. Silver 111K filas (datos del pipeline)

Requiere `SUPABASE_DB_URL` en `.env` (Session pooler, no Transaction pooler):

```bash
# Carga completa (Silver + geometrías + predicciones sintéticas)
python scripts/seed_supabase.py

# Solo cargar Silver parquet (111,606 filas vía COPY)
python scripts/seed_supabase.py --solo silver

# Solo geometrías F2 (UPZ) y F4 (cuadrantes)
python scripts/seed_supabase.py --solo geo
```

> Si `SUPABASE_DB_URL` no está disponible, el script usa batches via PostgREST (más lento, ~10 min para 111K filas).

**Verificar:** `scripts/seed_supabase.py` reporta `pg_database_size` al final. Debe quedar < 500MB (free tier limit).

### 4b. Corpus GraphRAG (F9 boletines SCJ + F10 RSS)

Requiere que el pipeline ETL haya descargado los archivos primero:

```bash
# Primero descargar corpus (si no están en datos/raw/)
python src/pipeline.py --source f9 f10

# Indexar: pdfplumber + feedparser → chunks → MiniLM embeddings → pgvector
python scripts/index_corpus.py
```

**Resultado esperado:** N chunks indexados (>100 con corpus real; con corpus vacío, seed 10-20 chunks de prueba para que `/graphrag` sea demostrable).

---

## Nivel 5 — Verificación E2E completa (pre-demo)

Con el servidor corriendo localmente:

```bash
cd backend
uvicorn app.main:app --reload  # AUTH_MODE=disabled para desarrollo
```

Secuencia de verificación con curl:

```bash
# 1. Health (sin auth)
curl http://localhost:8000/health
# → {"status": "ok"}

# 2. Predict (con AUTH_MODE=disabled usa usuario dev ADMIN)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"upz_cod": "044", "anio": 2026, "mes": 7}'
# → {"nivel_riesgo": "...", "probabilidades": {...}, "origen": "seed_dev"}

# 3. Explain
curl "http://localhost:8000/explain?upz_cod=044&anio=2026&mes=7"
# → {"shap_top": [...]}

# 4. Prescribe
curl -X POST http://localhost:8000/prescribe \
  -H "Content-Type: application/json" \
  -d '{"upz_cod": "044", "shap_top": [{"feature": "cuadrantes_por_km2", "valor": -0.34}]}'
# → {"diagnosticos": [...], "cai": {...}, "recomendacion_llm": "..."}

# 5. GraphRAG (requiere OPENROUTER_API_KEY o falla con degradación elegante)
curl -X POST http://localhost:8000/graphrag \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Por qué aumentó el hurto en Kennedy?"}'
# → {"respuesta": "...", "fuentes": [...]}

# 6. Whoami (requiere token real si AUTH_MODE=enabled)
curl http://localhost:8000/whoami \
  -H "Authorization: Bearer <token>"
# → {"rol": "...", "cuadrante_asignado": null, "cuadrante_pendiente": false}
```

**Presupuestos de latencia:** /health < 50ms · /predict < 500ms · /graphrag < 2s (2ª llamada cacheada ~100ms).

---

## Switch a artefactos reales (post Notebook 04)

Cuando el Notebook 04 genere el XGBoost real + SHAP values:

```bash
python scripts/load_model_artifacts.py \
  --predicciones datos/modelos/predicciones_xgboost.parquet \
  --shap datos/modelos/shap_values.parquet
```

Esto reemplaza `origen='seed_dev'` por `origen='notebook_04'` en Supabase. El backend no cambia — el lookup funciona igual.

---

## Checklist de verificación antes del demo (día D)

```
[ ] SUPABASE_URL + SERVICE_KEY + JWT_SECRET en .env de Railway (variables de entorno)
[ ] OPENROUTER_API_KEY en Railway
[ ] custom_access_token_hook habilitado en Dashboard → Auth → Hooks
[ ] pytest tests/ -m "not integration" → 31 passed
[ ] test_jwt_e2e.py -m integration → 1 passed (E3)
[ ] GET /health → 200 en Railway
[ ] POST /predict UPZ 044 → nivel_riesgo != null, origen='notebook_04'
[ ] POST /graphrag → respuesta con ≥1 cita (corpus indexado)
[ ] scripts/load_model_artifacts.py corrido (artefactos Notebook 04 cargados)
```
