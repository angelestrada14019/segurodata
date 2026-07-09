import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import { obtenerPeriodoMasReciente } from "@/lib/periodo-predicciones";
import type { LocalidadFeatureCollection } from "@/types/deck";

/**
 * Geometrías agregadas por localidad + riesgo dominante vía RPC
 * `localidades_geojson` (migración 0012). Usado cuando `use-zoom-adaptativo`
 * resuelve `'localidad'` (zoom < ZOOM_THRESHOLD). Mismo criterio de período
 * que `use-upz-geometrias` — ver comentario ahí y en
 * `lib/periodo-predicciones.ts`.
 */
export function useLocalidadesGeometrias(anio?: number, mes?: number) {
  return useQuery({
    queryKey: queryKeys.localidadesGeometrias.byPeriodo(anio, mes),
    queryFn: async (): Promise<LocalidadFeatureCollection> => {
      const periodo =
        anio !== undefined && mes !== undefined
          ? { anio, mes }
          : await obtenerPeriodoMasReciente();

      const { data, error } = await supabase.rpc("localidades_geojson", {
        p_anio: periodo?.anio ?? null,
        p_mes: periodo?.mes ?? null,
      });
      if (error) throw error;
      return data as LocalidadFeatureCollection;
    },
    staleTime: anio !== undefined && mes !== undefined ? Infinity : 5 * 60_000,
  });
}
