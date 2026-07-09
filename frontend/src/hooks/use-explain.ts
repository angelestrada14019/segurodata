import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";

// TODO(Sprint 2): consumir desde el modal de 5 pestañas (pestaña Predicción,
// SHAP top-3 o completo según rol). Contrato: GET /explain.
export function useExplain(upzCod: string, anio: number, mes: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.explain(upzCod, anio, mes),
    queryFn: () => apiClient.explain(upzCod, anio, mes),
    enabled,
  });
}
