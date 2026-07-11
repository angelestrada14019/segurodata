import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type { AsignarCuadranteRequest } from "@/types/api";

export function useAdminAsignarCuadrante() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      body,
    }: {
      userId: string;
      body: AsignarCuadranteRequest;
    }) => apiClient.asignarCuadrante(userId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminUsuarios.all });
    },
  });
}
