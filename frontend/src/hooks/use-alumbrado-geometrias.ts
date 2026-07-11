import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { AlumbradoFeatureCollection } from "@/types/deck";

/**
 * Alumbrado público por UPZ (F14) vía RPC `alumbrado_geojson` (migración
 * `20260710_0016_infraestructura_puntual.sql`) — reusa la geometría de
 * `upz_geometrias`, agrega `luminarias_led_upz` como propiedad. Capa
 * opcional del mapa (`panel-capas.tsx` → `capa-alumbrado.tsx`).
 *
 * Mismo patrón que `use-cuadrantes-geometrias.ts`: RPC `SECURITY INVOKER`,
 * `GRANT` solo a `authenticated` — `habilitado` debe combinar "checkbox
 * activado" AND "hay sesión" (lo resuelve `mapa-riesgo.tsx` con `useAuth()`).
 */
export function useAlumbradoGeometrias(habilitado: boolean) {
  return useQuery({
    queryKey: queryKeys.alumbradoGeometrias.all,
    queryFn: async (): Promise<AlumbradoFeatureCollection> => {
      const { data, error } = await supabase.rpc("alumbrado_geojson");
      if (error) throw error;
      return data as AlumbradoFeatureCollection;
    },
    enabled: habilitado,
    staleTime: 10 * 60_000,
  });
}
