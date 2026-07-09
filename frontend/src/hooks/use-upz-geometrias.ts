import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import { obtenerPeriodoMasReciente } from "@/lib/periodo-predicciones";
import type { UpzFeatureCollection } from "@/types/deck";

/**
 * Geometrías + riesgo de las 112 UPZs vía RPC `upz_geojson` (migración 0012).
 *
 * Si no se pasan `anio`/`mes`, resuelve primero el período más reciente
 * disponible en `predicciones` (ver `lib/periodo-predicciones.ts` — NUNCA se
 * llama la RPC con p_anio/p_mes ambos NULL, produciría Features duplicados
 * por UPZ). `staleTime: Infinity` cuando el período queda fijo — la
 * geometría no cambia y el riesgo de un mes ya cerrado tampoco.
 */
export function useUpzGeometrias(anio?: number, mes?: number) {
  return useQuery({
    queryKey: queryKeys.upzGeometrias.byPeriodo(anio, mes),
    queryFn: async (): Promise<UpzFeatureCollection> => {
      const periodo =
        anio !== undefined && mes !== undefined
          ? { anio, mes }
          : await obtenerPeriodoMasReciente();

      const { data, error } = await supabase.rpc("upz_geojson", {
        p_anio: periodo?.anio ?? null,
        p_mes: periodo?.mes ?? null,
      });
      if (error) throw error;
      return data as UpzFeatureCollection;
    },
    staleTime: anio !== undefined && mes !== undefined ? Infinity : 5 * 60_000,
  });
}
