-- SeguroData — Migración 0015: extender upsert_upz_geom con localidad
--
-- Hallazgo 10-jul: upz_geometrias.cod_localidad/nom_localidad estan NULL en las
-- 112 filas porque seed_geometrias() (scripts/seed_supabase.py) solo lee F2
-- (CODIGO_UPZ/NOMBRE/AREA_HECTAREAS, sin localidad — confirmado contra el
-- servicio ArcGIS real de IDECA/Catastro, el layer no tiene ese atributo) y el
-- RPC upsert_upz_geom (migracion 0010) nunca acepto esos parametros. El mapeo
-- real ya existe y ya funciona en Silver (src/transform.py, ahora tambien en
-- src/geo_utils.py) via F5 NUSE, que trae COD_LOCALIDAD/LOCALIDAD por incidente.
--
-- Esta migracion solo extiende el RPC — el backfill real de las 112 filas lo
-- hace scripts/seed_supabase.py --solo geo en un paso aparte.

-- DROP explícito: CREATE OR REPLACE con una lista de parámetros distinta crea
-- un OVERLOAD nuevo en vez de reemplazar la función original (Postgres
-- identifica funciones por nombre+firma) — eso deja GRANT/REVOKE ambiguos
-- entre las dos versiones. Hay que quitar la firma vieja primero.
DROP FUNCTION IF EXISTS public.upsert_upz_geom(text, text, text);

CREATE OR REPLACE FUNCTION public.upsert_upz_geom(
  p_upz_cod text, p_upz_nombre text, p_wkt text,
  p_cod_localidad text DEFAULT NULL, p_nom_localidad text DEFAULT NULL
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO upz_geometrias (upz_cod, upz_nombre, geom, cod_localidad, nom_localidad)
  VALUES (p_upz_cod, p_upz_nombre, ST_Multi(ST_GeomFromText(p_wkt, 4326)),
          p_cod_localidad, p_nom_localidad)
  ON CONFLICT (upz_cod) DO UPDATE
    SET geom          = EXCLUDED.geom,
        upz_nombre    = EXCLUDED.upz_nombre,
        -- COALESCE, no EXCLUDED directo: una llamada futura sin estos
        -- parametros (p.ej. un reseed de solo geometria) nunca debe borrar
        -- un valor de localidad ya backfillado.
        cod_localidad = COALESCE(EXCLUDED.cod_localidad, upz_geometrias.cod_localidad),
        nom_localidad = COALESCE(EXCLUDED.nom_localidad, upz_geometrias.nom_localidad);
END;
$$;
GRANT EXECUTE ON FUNCTION public.upsert_upz_geom TO service_role;
REVOKE EXECUTE ON FUNCTION public.upsert_upz_geom FROM authenticated, anon, public;
