-- SeguroData — Migración 0003: tablas geoespaciales (PostGIS)
-- upz_geometrias: F2 IDECA (112 UPZ). cuadrantes_geom: F4 MEBOG (599 cuadrantes).
-- upz_codes[] en cuadrantes_geom se pre-computa en el seed (intersección espacial)
-- para que el backend filtre comandante-por-cuadrante sin ST_Intersects en runtime.

CREATE TABLE IF NOT EXISTS upz_geometrias (
  upz_cod        varchar PRIMARY KEY,
  upz_nombre     varchar,
  cod_localidad  varchar,
  nom_localidad  varchar,
  geom           geometry(MultiPolygon, 4326)
);
CREATE INDEX IF NOT EXISTS idx_upz_geom ON upz_geometrias USING GIST (geom);

CREATE TABLE IF NOT EXISTS cuadrantes_geom (
  cuadrante_id varchar PRIMARY KEY,
  nom_cai      varchar,
  geom         geometry(MultiPolygon, 4326),
  upz_codes    varchar[] NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_cuadrantes_geom ON cuadrantes_geom USING GIST (geom);
