import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";

/**
 * Llama GET /whoami — fuente de verdad de rol/cuadrante_asignado/cuadrante_pendiente.
 * NUNCA decodificar el JWT a mano en el cliente para el rol: el backend ya
 * resuelve el fallback si el hook de claims custom no está habilitado.
 *
 * `enabled: !!sesionActiva` — no tiene sentido llamar /whoami sin sesión
 * (401 garantizado), lo consume `AuthProvider` pasando ese flag.
 */
export function useWhoami(sesionActiva: boolean) {
  return useQuery({
    queryKey: queryKeys.whoami,
    queryFn: apiClient.whoami,
    enabled: sesionActiva,
    staleTime: 5 * 60_000,
    retry: false,
  });
}
