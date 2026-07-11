import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { CamaraFeatureCollection } from "@/types/deck";

/**
 * Geometrías de las 92 cámaras salvavidas SDM (F13) vía RPC `camaras_geojson`
 * (migración `20260710_0016_infraestructura_puntual.sql`) — capa opcional
 * del mapa (`panel-capas.tsx` → `capa-camaras.tsx`).
 *
 * Mismo patrón que `use-cuadrantes-geometrias.ts`: RPC `SECURITY INVOKER`,
 * `GRANT` solo a `authenticated` — `habilitado` debe combinar "checkbox
 * activado" AND "hay sesión" (lo resuelve `mapa-riesgo.tsx` con `useAuth()`).
 */
export function useCamarasGeometrias(habilitado: boolean) {
  return useQuery({
    queryKey: queryKeys.camarasGeometrias.all,
    queryFn: async (): Promise<CamaraFeatureCollection> => {
      const { data, error } = await supabase.rpc("camaras_geojson");
      if (error) throw error;
      return data as CamaraFeatureCollection;
    },
    enabled: habilitado,
    staleTime: 10 * 60_000,
  });
}
