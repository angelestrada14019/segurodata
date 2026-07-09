import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";

// TODO(Sprint 2): consumir desde el modal de 5 pestañas (pestaña Predicción).
// Contrato: POST /predict — ver skill backend-segurodata.
export function usePredict(upzCod: string, anio: number, mes: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.predict(upzCod, anio, mes),
    queryFn: () => apiClient.predict({ upz_cod: upzCod, anio, mes }),
    enabled,
  });
}
