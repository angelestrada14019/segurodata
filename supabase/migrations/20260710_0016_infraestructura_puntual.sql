-- SeguroData — Migración 0016: geometría de infraestructura para las 3 capas
-- del mapa marcadas "Pendiente de datos" (F8 TransMilenio, F13 Cámaras
-- Salvavidas, F14 Alumbrado). F8/F13 son puntos (mismo patrón que
-- cuadrantes_geom, migración 0003); F14 reutiliza la geometría de
-- upz_geometrias (ya viene agregado por UPZ, no hay puntos individuales) y
-- solo agrega el conteo de luminarias como tabla de atributos separada.

CREATE TABLE IF NOT EXISTS transmilenio_geom (
  estacion_id  varchar PRIMARY KEY,
  nombre       varchar,
  geom         geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_transmilenio_geom ON transmilenio_geom USING GIST (geom);

CREATE TABLE IF NOT EXISTS camaras_geom (
  camara_id    varchar PRIMARY KEY,
  nombre       varchar,
  direccion    varchar,
  localidad    varchar,
  geom         geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_camaras_geom ON camaras_geom USING GIST (geom);

-- Atributos de infraestructura por UPZ (F13/F14 agregados) — geometría vive
-- en upz_geometrias, esta tabla solo aporta los conteos para colorear la capa.
CREATE TABLE IF NOT EXISTS upz_infraestructura (
  upz_cod             varchar PRIMARY KEY REFERENCES upz_geometrias(upz_cod),
  n_camaras_upz        int NOT NULL DEFAULT 0,
  luminarias_led_upz  int NOT NULL DEFAULT 0
);

ALTER TABLE transmilenio_geom ENABLE ROW LEVEL SECURITY;
ALTER TABLE camaras_geom ENABLE ROW LEVEL SECURITY;
ALTER TABLE upz_infraestructura ENABLE ROW LEVEL SECURITY;

-- Mismo criterio que cuadrantes_geom (migración 0006): infraestructura
-- suplementaria del mapa, visible para usuarios autenticados, no para anon.
DROP POLICY IF EXISTS "transmilenio_autenticados" ON transmilenio_geom;
CREATE POLICY "transmilenio_autenticados" ON transmilenio_geom
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "camaras_autenticados" ON camaras_geom;
CREATE POLICY "camaras_autenticados" ON camaras_geom
  FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "upz_infraestructura_autenticados" ON upz_infraestructura;
CREATE POLICY "upz_infraestructura_autenticados" ON upz_infraestructura
  FOR SELECT TO authenticated USING (true);

-- RPCs GeoJSON (mismo patrón que cuadrantes_geojson, migración 0012):
-- SECURITY INVOKER, sin filtro de rol — la RLS de arriba ya restringe a
-- authenticated, y estas capas no exponen datos de riesgo por cuadrante.

CREATE OR REPLACE FUNCTION public.transmilenio_geojson()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(t.geom)::jsonb,
        'properties', jsonb_build_object(
          'estacion_id', t.estacion_id,
          'nombre', t.nombre
        )
      )
    ), '[]'::jsonb)
  )
  FROM transmilenio_geom t;
$$;
GRANT EXECUTE ON FUNCTION public.transmilenio_geojson TO authenticated;
REVOKE EXECUTE ON FUNCTION public.transmilenio_geojson FROM anon, public;

CREATE OR REPLACE FUNCTION public.camaras_geojson()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(c.geom)::jsonb,
        'properties', jsonb_build_object(
          'camara_id', c.camara_id,
          'nombre', c.nombre,
          'direccion', c.direccion,
          'localidad', c.localidad
        )
      )
    ), '[]'::jsonb)
  )
  FROM camaras_geom c;
$$;
GRANT EXECUTE ON FUNCTION public.camaras_geojson TO authenticated;
REVOKE EXECUTE ON FUNCTION public.camaras_geojson FROM anon, public;

CREATE OR REPLACE FUNCTION public.alumbrado_geojson()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(g.geom)::jsonb,
        'properties', jsonb_build_object(
          'upz_cod', g.upz_cod,
          'upz_nombre', g.upz_nombre,
          'luminarias_led_upz', coalesce(i.luminarias_led_upz, 0)
        )
      )
    ), '[]'::jsonb)
  )
  FROM upz_geometrias g
  LEFT JOIN upz_infraestructura i ON i.upz_cod = g.upz_cod;
$$;
GRANT EXECUTE ON FUNCTION public.alumbrado_geojson TO authenticated;
REVOKE EXECUTE ON FUNCTION public.alumbrado_geojson FROM anon, public;
