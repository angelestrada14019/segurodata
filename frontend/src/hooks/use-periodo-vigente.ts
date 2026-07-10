import { useQuery } from "@tanstack/react-query";
import { obtenerPeriodoMasReciente } from "@/lib/periodo-predicciones";
import { queryKeys } from "@/lib/query-keys";

/**
 * Resuelve el período (anio, mes) más reciente disponible en `predicciones`
 * — RPC `periodo_mas_reciente` (ver `lib/periodo-predicciones.ts`) cacheada
 * bajo `queryKeys.periodoVigente`.
 *
 * Hook compartido por `use-diagnostico-upz.ts` (predict+explain del modal
 * UPZ y de `routes/modulo3-prescriptivo.tsx`) y `use-top10-riesgo.ts`
 * (listado de `routes/modulo2-prediccion.tsx`) — mismo query key en ambos
 * consumidores, así que si el usuario ya abrió el modal o el mapa antes de
 * llegar a alguna de estas vistas, el período llega desde cache sin
 * round-trip nuevo a Supabase.
 */
export function usePeriodoVigente(habilitado = true) {
  return useQuery({
    queryKey: queryKeys.periodoVigente,
    queryFn: obtenerPeriodoMasReciente,
    enabled: habilitado,
    staleTime: 5 * 60_000,
  });
}
