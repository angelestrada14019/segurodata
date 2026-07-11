import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { TransmilenioFeatureCollection } from "@/types/deck";

/**
 * Geometrías de las 153 estaciones TransMilenio (F8) vía RPC
 * `transmilenio_geojson` (migración `20260710_0016_infraestructura_puntual.sql`)
 * — capa opcional del mapa (`panel-capas.tsx` → `capa-transmilenio.tsx`).
 *
 * Mismo patrón que `use-cuadrantes-geometrias.ts`: RPC `SECURITY INVOKER`,
 * `GRANT` solo a `authenticated` — `habilitado` debe combinar "checkbox
 * activado" AND "hay sesión" (lo resuelve `mapa-riesgo.tsx` con `useAuth()`).
 */
export function useTransmilenioGeometrias(habilitado: boolean) {
  return useQuery({
    queryKey: queryKeys.transmilenioGeometrias.all,
    queryFn: async (): Promise<TransmilenioFeatureCollection> => {
      const { data, error } = await supabase.rpc("transmilenio_geojson");
      if (error) throw error;
      return data as TransmilenioFeatureCollection;
    },
    enabled: habilitado,
    staleTime: 10 * 60_000,
  });
}
