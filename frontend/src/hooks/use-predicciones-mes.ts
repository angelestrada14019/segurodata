import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { PrediccionRow } from "@/types/supabase";

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
