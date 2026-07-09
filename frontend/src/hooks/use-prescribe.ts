import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { PrescribeRequest } from "@/types/api";

// TODO(Sprint 3): consumir desde el modal de 5 pestañas (pestaña Sugerencia).
// Contrato: POST /prescribe — requiere shap_top ya resuelto por useExplain.
export function usePrescribe() {
  return useMutation({
    mutationFn: (body: PrescribeRequest) => apiClient.prescribe(body),
  });
}
