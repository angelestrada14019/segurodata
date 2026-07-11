-- Migración 0019: upz_geojson()/localidades_geojson() (mapa de Módulo 1 —
-- Diagnóstico) dejan de filtrar por cuadrante_asignado para COMANDANTE_CAI.
--
-- Antes (migración 0006, replicado en estas 2 RPC SECURITY DEFINER):
-- CIUDADANO/ANALISTA_SDSCJ/ADMIN/anon veían las 112 UPZ; COMANDANTE_CAI solo
-- las de su cuadrante, el resto con nivel_riesgo NULL (pintado gris).
--
-- Por qué es un bug y no una decisión deliberada: un visitante SIN sesión ya
-- ve el mapa completo (rol IS NULL entra en la rama sin filtro) — restringir
-- justo al comandante AUTENTICADO, que es quien más necesita contexto de
-- ciudad completa para su trabajo operativo, no protege nada que el
-- visitante anónimo no vea ya. La restricción de cuadrante sigue intacta y
-- sin tocar donde sí es correcta: /predict y /prescribe (FastAPI,
-- backend/app/services/prediction_service.py) para las acciones puntuales
-- del comandante.

CREATE OR REPLACE FUNCTION public.upz_geojson(p_anio integer DEFAULT NULL::integer, p_mes integer DEFAULT NULL::integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
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
    AND (p_mes  IS NULL OR p.mes  = p_mes);
    -- Módulo 1 es diagnóstico de solo lectura para TODOS los roles (incluido
    -- anon) — migración 0019 quita el filtro de cuadrante que aquí no
    -- aportaba nada (ver comentario de la migración). COMANDANTE_CAI sigue
    -- restringido a su cuadrante en /predict y /prescribe, que sí son
    -- accionables.
END;
$function$;

CREATE OR REPLACE FUNCTION public.localidades_geojson(p_anio integer DEFAULT NULL::integer, p_mes integer DEFAULT NULL::integer)
 RETURNS jsonb
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN (
    SELECT jsonb_build_object(
      'type', 'FeatureCollection',
      'features', coalesce(jsonb_agg(
        jsonb_build_object(
          'type', 'Feature',
          'geometry', geom_union,
          'properties', jsonb_build_object(
            'cod_localidad', grp_cod,
            'nom_localidad', grp_nom,
            'nivel_riesgo', nivel_dominante
          )
        )
      ), '[]'::jsonb)
    )
    FROM (
      SELECT
        coalesce(g.cod_localidad, g.upz_cod) AS grp_cod,
        coalesce(g.nom_localidad, g.upz_nombre) AS grp_nom,
        ST_AsGeoJSON(ST_Union(g.geom))::jsonb AS geom_union,
        mode() WITHIN GROUP (ORDER BY p.nivel_riesgo) AS nivel_dominante
      FROM upz_geometrias g
      LEFT JOIN predicciones p
        ON p.upz_cod = g.upz_cod
        AND (p_anio IS NULL OR p.anio = p_anio)
        AND (p_mes  IS NULL OR p.mes  = p_mes)
        -- Ver comentario en upz_geojson() / migración 0019.
      GROUP BY coalesce(g.cod_localidad, g.upz_cod), coalesce(g.nom_localidad, g.upz_nombre)
    ) grupos
  );
END;
$function$;
