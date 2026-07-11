import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { PrescribeRequest } from "@/types/api";

export function usePrescribe() {
  return useMutation({
    mutationFn: (body: PrescribeRequest) => apiClient.prescribe(body),
  });
}
