import { supabase } from "@/lib/supabase";

/**
 * Resuelve el (anio, mes) más reciente disponible en `predicciones`.
 *
 * DECISIÓN DE DISEÑO (ver también `hooks/use-upz-geometrias.ts`): las RPCs
 * `upz_geojson`/`localidades_geojson` (migración 0012) NO devuelven "el mes
 * más reciente" cuando p_anio/p_mes son NULL — devuelven TODAS las filas de
 * `predicciones` que hagan match con cada upz_cod, sin restricción de
 * período. Si existe más de un mes histórico por UPZ, el `LEFT JOIN` produce
 * Features duplicados por UPZ dentro del mismo FeatureCollection (el
 * `jsonb_agg` de la función no des-duplica). Por eso el frontend SIEMPRE
 * resuelve primero el período más reciente y se lo pasa explícito a la RPC —
 * nunca se llama la RPC con ambos parámetros NULL en producción.
 *
 * BUG CORREGIDO (09-jul, migración 0013): esta función solía consultar
 * `predicciones` directo con supabase-js. La política RLS
 * `predicciones_por_rol` (migración 0006) es `FOR SELECT TO authenticated`
 * — un visitante `anon` (el caso de uso de `/diagnostico`, mapa público sin
 * login) recibía 0 filas en silencio, esta función devolvía `null`, y el
 * fallback a p_anio/p_mes=NULL disparaba el bug de duplicación descrito
 * arriba, excediendo el `statement_timeout` de 3s del rol `anon` (45s reales
 * medidos). Ahora usa la RPC `periodo_mas_reciente` (SECURITY DEFINER, mismo
 * patrón que `upz_geojson`), que expone únicamente `{anio, mes}` a anon.
 */
export async function obtenerPeriodoMasReciente(): Promise<{
  anio: number;
  mes: number;
} | null> {
  const { data, error } = await supabase.rpc("periodo_mas_reciente");

  if (error) throw error;
  if (!data) return null;
  return { anio: data.anio, mes: data.mes };
}
