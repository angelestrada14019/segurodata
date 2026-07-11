-- Upsert geometría estación TransMilenio desde WKT (mismo patrón que
-- upsert_upz_geom/upsert_cuadrante_geom, migración 0010, pero sin ST_Multi
-- porque el destino es geometry(Point, 4326), no MultiPolygon).
CREATE OR REPLACE FUNCTION public.upsert_transmilenio_geom(
  p_estacion_id text, p_nombre text, p_wkt text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO transmilenio_geom (estacion_id, nombre, geom)
  VALUES (p_estacion_id, p_nombre, ST_GeomFromText(p_wkt, 4326))
  ON CONFLICT (estacion_id) DO UPDATE
    SET geom = EXCLUDED.geom, nombre = EXCLUDED.nombre;
END;
$$;
GRANT EXECUTE ON FUNCTION public.upsert_transmilenio_geom TO service_role;
REVOKE EXECUTE ON FUNCTION public.upsert_transmilenio_geom FROM authenticated, anon, public;

CREATE OR REPLACE FUNCTION public.upsert_camara_geom(
  p_camara_id text, p_nombre text, p_direccion text, p_localidad text, p_wkt text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO camaras_geom (camara_id, nombre, direccion, localidad, geom)
  VALUES (p_camara_id, p_nombre, p_direccion, p_localidad, ST_GeomFromText(p_wkt, 4326))
  ON CONFLICT (camara_id) DO UPDATE
    SET geom      = EXCLUDED.geom,
        nombre    = EXCLUDED.nombre,
        direccion = EXCLUDED.direccion,
        localidad = EXCLUDED.localidad;
END;
$$;
GRANT EXECUTE ON FUNCTION public.upsert_camara_geom TO service_role;
REVOKE EXECUTE ON FUNCTION public.upsert_camara_geom FROM authenticated, anon, public;
