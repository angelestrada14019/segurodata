import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { CuadranteFeatureCollection } from "@/types/deck";

/**
 * Geometrías completas de los cuadrantes de policía vía RPC
 * `cuadrantes_geojson` (migración 0012) — capa opcional del mapa
 * (`panel-capas.tsx` → `capa-cuadrantes.tsx`).
 *
 * La RPC es `SECURITY INVOKER`, `GRANT` solo a `authenticated` (`REVOKE`
 * explícito de `anon`) — un visitante público de /diagnostico simplemente no
 * puede activar esta capa (degradación aceptable, documentada en la propia
 * migración 0012). `habilitado` debe combinar "checkbox activado" AND "hay
 * sesión" (lo resuelve el consumidor, `mapa-riesgo.tsx`, con `useAuth()`) —
 * evita disparar la RPC (y su error 42501 de permisos) para sesiones sin
 * login, mismo patrón que `usePeriodoVigente(habilitado)`.
 */
export function useCuadrantesGeometrias(habilitado: boolean) {
  return useQuery({
    queryKey: queryKeys.cuadrantesGeometrias.all,
    queryFn: async (): Promise<CuadranteFeatureCollection> => {
      const { data, error } = await supabase.rpc("cuadrantes_geojson");
      if (error) throw error;
      return data as CuadranteFeatureCollection;
    },
    enabled: habilitado,
    staleTime: 10 * 60_000,
  });
}
