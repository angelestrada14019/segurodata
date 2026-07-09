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
 * resuelve primero el período más reciente con esta query directa y se lo
 * pasa explícito a la RPC — nunca se llama la RPC con ambos parámetros NULL
 * en producción.
 */
export async function obtenerPeriodoMasReciente(): Promise<{
  anio: number;
  mes: number;
} | null> {
  const { data, error } = await supabase
    .from("predicciones")
    .select("anio, mes")
    .order("anio", { ascending: false })
    .order("mes", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;
  return { anio: data.anio, mes: data.mes };
}
