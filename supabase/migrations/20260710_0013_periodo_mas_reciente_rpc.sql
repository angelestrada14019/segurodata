-- SeguroData — Migración 0013: RPC periodo_mas_reciente (fix bug bloqueante 09-jul)
--
-- Bug: el frontend (lib/periodo-predicciones.ts) resolvía el período más reciente
-- consultando `predicciones` directo con supabase-js. La política RLS
-- "predicciones_por_rol" (migración 0006) es `FOR SELECT TO authenticated` — un
-- visitante anon (el caso de uso exacto de /diagnostico, "acceso público sin login")
-- recibe 0 filas, no un error. `obtenerPeriodoMasReciente()` entonces retorna null,
-- y use-upz-geometrias.ts/use-localidades-geometrias.ts caen al fallback
-- p_anio=NULL/p_mes=NULL — que dispara un bug de duplicación de filas ya documentado
-- en el propio código (LEFT JOIN sin filtro de período = ~16 filas por UPZ en vez de 1,
-- 1791 filas totales medidas) y excede el statement_timeout de 3s del rol anon
-- (45s medidos con EXPLAIN ANALYZE). Resultado: mapa público en blanco con error 500.
--
-- Fix: mismo patrón SECURITY DEFINER que ya usa upz_geojson/localidades_geojson
-- (migración 0012) — expone SOLO {anio, mes}, no filas de predicciones.

CREATE OR REPLACE FUNCTION public.periodo_mas_reciente()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
  SELECT jsonb_build_object('anio', anio, 'mes', mes)
  FROM predicciones
  ORDER BY anio DESC, mes DESC
  LIMIT 1;
$$;
GRANT EXECUTE ON FUNCTION public.periodo_mas_reciente TO anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.periodo_mas_reciente FROM public;
