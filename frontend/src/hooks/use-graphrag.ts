import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { GraphragRequest } from "@/types/api";

export function useGraphrag() {
  return useMutation({
    mutationFn: (body: GraphragRequest) => apiClient.graphrag(body),
  });
}
