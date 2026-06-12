-- SeguroData — Migración 0002: tablas core
-- silver_upz_mes refleja datos/procesados/silver_upz_mes.parquet (20 cols actuales
-- + 3 columnas F11/F13/F14 nullable que llegan en Notebook 03).
-- predicciones y shap_values llevan columna `origen`: 'seed_dev' (sintético) | 'notebook_04' (real).

CREATE TABLE IF NOT EXISTS silver_upz_mes (
  id                    bigserial PRIMARY KEY,
  upz_cod               varchar NOT NULL,
  anio                  int NOT NULL,
  mes                   int NOT NULL,
  tipo_crimen           varchar,
  es_crimen             boolean,
  n_delitos             int,
  n_delitos_upz_4sem    int,
  n_delitos_upz_8sem    int,
  cod_localidad         varchar,
  nom_localidad         varchar,
  temperatura_c         double precision,
  precipitacion_mm_mes  double precision,
  n_incidentes_nuse     int,
  ratio_tipo_nuse_total double precision,
  estrato_promedio_upz  double precision,
  cuadrantes_por_km2    double precision,
  area_upz_km2          double precision,
  n_estaciones_tm       int,
  dist_tm_metros        double precision,
  es_mitad_anio         boolean,
  km_via_intervenida_upz double precision,   -- F11 (Notebook 03)
  n_camaras_upz         int,                  -- F13 (Notebook 03)
  luminarias_led_upz    int                   -- F14 (Notebook 03)
);
CREATE INDEX IF NOT EXISTS idx_silver_upz_mes ON silver_upz_mes (upz_cod, anio, mes);

CREATE TABLE IF NOT EXISTS predicciones (
  upz_cod      varchar NOT NULL,
  anio         int NOT NULL,
  mes          int NOT NULL CHECK (mes BETWEEN 1 AND 12),
  nivel_riesgo varchar NOT NULL CHECK (nivel_riesgo IN ('CRITICO','ALTO','MEDIO','BAJO')),
  prob_critico double precision NOT NULL DEFAULT 0,
  prob_alto    double precision NOT NULL DEFAULT 0,
  prob_medio   double precision NOT NULL DEFAULT 0,
  prob_bajo    double precision NOT NULL DEFAULT 0,
  origen       varchar NOT NULL DEFAULT 'seed_dev' CHECK (origen IN ('seed_dev','notebook_04')),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (upz_cod, anio, mes)
);

CREATE TABLE IF NOT EXISTS shap_values (
  upz_cod  varchar NOT NULL,
  anio     int NOT NULL,
  mes      int NOT NULL CHECK (mes BETWEEN 1 AND 12),
  feature  varchar NOT NULL,
  valor    double precision NOT NULL,
  origen   varchar NOT NULL DEFAULT 'seed_dev' CHECK (origen IN ('seed_dev','notebook_04')),
  PRIMARY KEY (upz_cod, anio, mes, feature)
);

CREATE TABLE IF NOT EXISTS change_points (
  id            bigserial PRIMARY KEY,
  localidad_cod varchar NOT NULL,
  localidad_nom varchar,
  fecha_ruptura date NOT NULL,
  tipo_cambio   varchar CHECK (tipo_cambio IN ('ALZA','BAJA','INDEFINIDO')),
  magnitude     double precision
);
