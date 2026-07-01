-- SeguroData — Migración 0012: RPCs GeoJSON para el mapa deck.gl del frontend (Fase 3)
--
-- supabase-js no parsea el tipo `geometry` de PostGIS (WKB) directamente — estas 3
-- funciones devuelven GeoJSON ya construido en Postgres via ST_AsGeoJSON.
--
-- upz_geojson y localidades_geojson son SECURITY DEFINER con filtro de rol/cuadrante
-- EXPLÍCITO en el cuerpo (replica exactamente la política `predicciones_por_rol` de
-- la migración 0006) — NO por comodidad: esa política es `TO authenticated` únicamente,
-- así que un SECURITY INVOKER dejaría el mapa público (Módulo 1, "lectura sin login")
-- completamente gris para cualquier visitante anónimo, porque RLS bloquearía el JOIN
-- con `predicciones` por completo para el rol `anon`. Mismo patrón D8 que ya usa el
-- backend ("el filtro por rol/cuadrante va EXPLÍCITO en código cuando RLS no cubre el
-- caso real") — aquí se replica la MISMA regla que la política ya aplica para
-- authenticated, y se añade la rama pública para anon.
--
-- cuadrantes_geojson SÍ es SECURITY INVOKER sin filtro especial: no expone datos de
-- riesgo, solo la política existente `cuadrantes_autenticados` (authenticated, sin
-- restricción de rol) aplica tal cual — un visitante anónimo simplemente no ve esa
-- capa opcional, degradación aceptable (no es el mapa base).

CREATE OR REPLACE FUNCTION public.upz_geojson(p_anio int DEFAULT NULL, p_mes int DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rol text := auth.jwt()->>'rol';
  v_cuadrante text := auth.jwt()->>'cuadrante_asignado';
BEGIN
  RETURN jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(g.geom)::jsonb,
        'properties', jsonb_build_object(
          'upz_cod', g.upz_cod,
          'upz_nombre', g.upz_nombre,
          'cod_localidad', g.cod_localidad,
          'nom_localidad', g.nom_localidad,
          'nivel_riesgo', p.nivel_riesgo,
          'prob_critico', p.prob_critico,
          'prob_alto', p.prob_alto,
          'prob_medio', p.prob_medio,
          'prob_bajo', p.prob_bajo
        )
      )
    ), '[]'::jsonb)
  )
  FROM upz_geometrias g
  LEFT JOIN predicciones p
    ON p.upz_cod = g.upz_cod
    AND (p_anio IS NULL OR p.anio = p_anio)
    AND (p_mes  IS NULL OR p.mes  = p_mes)
    -- Replica predicciones_por_rol (migración 0006): anon (mapa público)/CIUDADANO/
    -- ANALISTA_SDSCJ/ADMIN ven todas las UPZ; COMANDANTE_CAI solo las de su cuadrante;
    -- sin match -> nivel_riesgo NULL (el frontend pinta gris "sin datos", nunca inventa color).
    AND (
      v_rol IS NULL
      OR v_rol IN ('CIUDADANO','ANALISTA_SDSCJ','ADMIN')
      OR (v_rol = 'COMANDANTE_CAI' AND p.upz_cod IN (
            SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
            WHERE cg.cuadrante_id = v_cuadrante
          ))
    );
END;
$$;
GRANT EXECUTE ON FUNCTION public.upz_geojson TO anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.upz_geojson FROM public;

CREATE OR REPLACE FUNCTION public.localidades_geojson(p_anio int DEFAULT NULL, p_mes int DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rol text := auth.jwt()->>'rol';
  v_cuadrante text := auth.jwt()->>'cuadrante_asignado';
BEGIN
  RETURN jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(ST_Union(g.geom))::jsonb,
        'properties', jsonb_build_object(
          'cod_localidad', g.cod_localidad,
          'nom_localidad', g.nom_localidad,
          'nivel_riesgo', mode() WITHIN GROUP (ORDER BY p.nivel_riesgo)
        )
      )
    ), '[]'::jsonb)
  )
  FROM upz_geometrias g
  LEFT JOIN predicciones p
    ON p.upz_cod = g.upz_cod
    AND (p_anio IS NULL OR p.anio = p_anio)
    AND (p_mes  IS NULL OR p.mes  = p_mes)
    AND (
      v_rol IS NULL
      OR v_rol IN ('CIUDADANO','ANALISTA_SDSCJ','ADMIN')
      OR (v_rol = 'COMANDANTE_CAI' AND p.upz_cod IN (
            SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
            WHERE cg.cuadrante_id = v_cuadrante
          ))
    )
  GROUP BY g.cod_localidad, g.nom_localidad;
END;
$$;
GRANT EXECUTE ON FUNCTION public.localidades_geojson TO anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.localidades_geojson FROM public;

CREATE OR REPLACE FUNCTION public.cuadrantes_geojson()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public
AS $$
  SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', coalesce(jsonb_agg(
      jsonb_build_object(
        'type', 'Feature',
        'geometry', ST_AsGeoJSON(cg.geom)::jsonb,
        'properties', jsonb_build_object(
          'cuadrante_id', cg.cuadrante_id,
          'nom_cai', cg.nom_cai,
          'telefono', cg.telefono
        )
      )
    ), '[]'::jsonb)
  )
  FROM cuadrantes_geom cg;
$$;
GRANT EXECUTE ON FUNCTION public.cuadrantes_geojson TO authenticated;
REVOKE EXECUTE ON FUNCTION public.cuadrantes_geojson FROM anon, public;
