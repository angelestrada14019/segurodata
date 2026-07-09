import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { GraphragRequest } from "@/types/api";

// TODO(Sprint 3): consumir desde el modal de 5 pestañas (pestaña Chatbot) y
// desde /chatbot standalone. Contrato: POST /graphrag.
export function useGraphrag() {
  return useMutation({
    mutationFn: (body: GraphragRequest) => apiClient.graphrag(body),
  });
}
