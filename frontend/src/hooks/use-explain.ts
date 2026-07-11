import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";

export function useExplain(upzCod: string, anio: number, mes: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.explain(upzCod, anio, mes),
    queryFn: () => apiClient.explain(upzCod, anio, mes),
    enabled,
  });
}
