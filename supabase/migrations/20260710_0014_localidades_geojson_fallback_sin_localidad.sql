-- SeguroData — Migración 0014: fallback en localidades_geojson cuando falta cod_localidad
--
-- Hallazgo 09-jul (verificacion Checkpoint 1 frontend): upz_geometrias tiene
-- cod_localidad/nom_localidad NULL en las 112 filas — el pipeline F2 (shapefile
-- IDECA) nunca trajo el codigo de localidad, solo CODIGO_UPZ/NOMBRE/AREA_HECTAREAS.
-- Con GROUP BY cod_localidad NULL, la funcion original (migración 0012) colapsaba
-- las 112 UPZs en UNA sola feature fusionada (ST_Union de todo Bogota) — el mapa
-- por defecto (zoom<12, la vista con la que arranca /diagnostico) se veia como un
-- blob roto.
--
-- Fix acotado: agrupar por coalesce(cod_localidad, upz_cod) — cuando no hay
-- localidad real, cada UPZ es su propio grupo (112 features reales coloreadas
-- en vez de 1 blob). No inventa nombres/limites de localidad. El backfill real
-- del mapeo oficial UPZ->Localidad de Bogota queda pendiente como tarea de
-- pipeline de datos aparte.
--
-- Nota tecnica: la agregacion por grupo (ST_Union + mode()) vive en una
-- subconsulta separada del jsonb_agg externo — Postgres no permite anidar
-- mode() WITHIN GROUP dentro de jsonb_agg() en la misma query cuando hay más
-- de un grupo resultante ("aggregate function calls cannot be nested"); con
-- el bug original (1 solo grupo) ese error quedaba enmascarado.

CREATE OR REPLACE FUNCTION public.localidades_geojson(p_anio int DEFAULT NULL, p_mes int DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rol text := auth.jwt()->>'rol';
  v_cuadrante text := auth.jwt()->>'cuadrante_asignado';
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
        AND (
          v_rol IS NULL
          OR v_rol IN ('CIUDADANO','ANALISTA_SDSCJ','ADMIN')
          OR (v_rol = 'COMANDANTE_CAI' AND p.upz_cod IN (
                SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
                WHERE cg.cuadrante_id = v_cuadrante
              ))
        )
      GROUP BY coalesce(g.cod_localidad, g.upz_cod), coalesce(g.nom_localidad, g.upz_nombre)
    ) grupos
  );
END;
$$;
GRANT EXECUTE ON FUNCTION public.localidades_geojson TO anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.localidades_geojson FROM public;
