import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { PrediccionRow } from "@/types/supabase";

// TODO(Sprint 2): consumir desde el slider-temporal.tsx (Módulo 1) para
// listar meses disponibles / precargar predicciones de un período.
export function usePrediccionesMes(anio: number, mes: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.prediccionesMes(anio, mes),
    queryFn: async (): Promise<PrediccionRow[]> => {
      const { data, error } = await supabase
        .from("predicciones")
        .select("*")
        .eq("anio", anio)
        .eq("mes", mes);
      if (error) throw error;
      return data;
    },
    enabled,
  });
}
