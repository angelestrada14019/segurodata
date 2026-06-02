---
name: supabase-segurodata
description: Schema y configuración de Supabase para SeguroData — tablas, RLS, pgvector, PostGIS y Realtime.
---

# Supabase SeguroData — Schema del Proyecto

Referencia completa del schema de Supabase: tablas, extensiones, índices y políticas RLS.

## Extensiones requeridas

```sql
-- Habilitar en Supabase Dashboard → SQL Editor
CREATE EXTENSION IF NOT EXISTS postgis;    -- geometrías UPZ
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector para embeddings GraphRAG
```

## Tablas del sistema

### `silver_upz_mes` — datos del pipeline (cargada desde Silver parquet)
```sql
CREATE TABLE silver_upz_mes (
  id              bigserial PRIMARY KEY,
  upz_cod         varchar NOT NULL,
  anio            int,
  mes             int,
  tipo_crimen     varchar,
  es_crimen       boolean,
  cod_localidad   varchar,
  nom_localidad   varchar,
  n_delitos       int,
  n_delitos_upz_4sem int,
  n_delitos_upz_8sem int,
  tipo_delito_dominante varchar,
  franja_dominante_mes varchar,
  n_incidentes_nuse int,
  ratio_nuse_delitos_upz float,
  temperatura_c   float,
  precipitacion_mm_mes float,
  estrato_promedio_upz float,
  cuadrantes_por_km2 float,
  n_estaciones_tm int,
  dist_tm_metros  float,
  km_via_intervenida_upz float,
  n_camaras_upz   int,
  luminarias_led_upz int
);
CREATE INDEX idx_silver_upz_mes ON silver_upz_mes (upz_cod, anio, mes);
```

### `shap_values` — SHAP pre-computados (Notebook 04)
```sql
CREATE TABLE shap_values (
  upz_cod varchar,
  anio    int,
  mes     int,
  nivel_riesgo varchar,        -- predicción XGBoost para ese período
  shap_cuadrantes_por_km2 float,
  shap_estrato_promedio_upz float,
  shap_luminarias_led_upz float,
  shap_n_camaras_upz float,
  shap_km_via_intervenida_upz float,
  shap_n_delitos_upz_4sem float,
  shap_temperatura_c float,
  shap_ratio_nuse_criminal_upz float,
  -- ... resto de features
  PRIMARY KEY (upz_cod, anio, mes)
);
```

### `upz_geometrias` — polígonos UPZ (PostGIS)
```sql
CREATE TABLE upz_geometrias (
  upz_cod        varchar PRIMARY KEY,
  upz_nombre     varchar,
  cod_localidad  varchar,
  nom_localidad  varchar,
  geom           geometry(Polygon, 4326)
);
CREATE INDEX idx_upz_geom ON upz_geometrias USING GIST (geom);
```

### `change_points` — puntos de ruptura ruptures (F1 DAI)
```sql
CREATE TABLE change_points (
  localidad_cod  varchar,
  localidad_nom  varchar,
  mes_ruptura    int,       -- mes en que se detectó el cambio (1-93 para 2018-2026)
  fecha_ruptura  date,
  tipo_cambio    varchar,   -- 'ALZA' | 'BAJA' | 'INDEFINIDO'
  magnitude      float
);
```

### `documents` — corpus GraphRAG (F9+F10, pgvector)
```sql
CREATE TABLE documents (
  id        bigserial PRIMARY KEY,
  content   text,
  source    varchar,        -- 'SCJ_BOLETIN' | 'RSS_ELTIEMPO' | 'RSS_ESPECTADOR' | 'RSS_INFORMANTE'
  fecha     date,
  upz_cod   varchar,        -- nullable — si el doc es específico de una UPZ
  embedding vector(384)     -- all-MiniLM-L6-v2 (sentence-transformers)
);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- Función RPC para búsqueda por similaridad
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_upz varchar DEFAULT NULL
)
RETURNS TABLE (id bigint, content text, source varchar, similarity float)
LANGUAGE sql AS $$
  SELECT id, content, source,
         1 - (embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE (filter_upz IS NULL OR upz_cod = filter_upz)
    AND 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### `alarmas_ciudadanas` — sistema de alarmas (ideas/plataforma-ciudadana)
```sql
-- Tabla para la feature de alarmas ciudadanas en tiempo real
-- Ver docs/ideas_plataforma_ciudadana.md — Idea #4
CREATE TABLE alarmas_ciudadanas (
  id           uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      uuid REFERENCES auth.users,
  lat          float NOT NULL,
  lon          float NOT NULL,
  upz_cod      varchar,
  cuadrante_id varchar,
  tipo         varchar CHECK (tipo IN ('REPORTE', 'PANICO')),
  estado       varchar DEFAULT 'ACTIVA'
               CHECK (estado IN ('ACTIVA', 'ATENDIDA', 'FALSA_ALARMA')),
  created_at   timestamptz DEFAULT now()
);
-- Habilitar Realtime para esta tabla en Supabase Dashboard
```

## Scripts de carga

```bash
# Orden correcto de ejecución:
python scripts/setup_supabase.py    # crea todas las tablas + extensiones
python scripts/load_geometrias.py   # carga 112 polígonos UPZ (F2)
python scripts/load_silver.py       # carga silver_upz_mes.parquet
python scripts/load_predictions.py  # carga predicciones XGBoost
python scripts/load_shap.py         # carga SHAP pre-computados
python scripts/index_corpus.py      # genera embeddings + carga en documents
```

## Row Level Security (RLS) — para las ideas de roles

```sql
-- Habilitar RLS en las tablas sensibles
ALTER TABLE shap_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE alarmas_ciudadanas ENABLE ROW LEVEL SECURITY;

-- Política ejemplo: comandante ve solo su cuadrante
CREATE POLICY "comandante ve su cuadrante"
  ON alarmas_ciudadanas FOR SELECT
  USING (cuadrante_id = (
    SELECT cuadrante_asignado FROM user_profiles WHERE user_id = auth.uid()
  ));
```

## Conexión desde Python (backend FastAPI)

```python
from supabase import create_client
import os

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]  # service key para el backend
)

# Ejemplo: cargar SHAP de una UPZ
shap = supabase.table("shap_values").select("*").eq("upz_cod", "044").eq("mes", 7).execute()
```

## Conexión desde React (frontend)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY   // clave pública — no tiene permisos de escritura sensible
)

// Ejemplo: Realtime para alarmas del cuadrante
supabase.channel('cuadrante-048')
  .on('postgres_changes', { event: 'INSERT', table: 'alarmas_ciudadanas',
      filter: 'cuadrante_id=eq.048' },
    (payload) => console.log('Nueva alarma:', payload.new))
  .subscribe()
```
