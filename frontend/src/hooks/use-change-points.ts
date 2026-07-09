import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { ChangePointRow } from "@/types/supabase";

// TODO(Sprint 2): consumir desde Módulo 1 — Diagnóstico (rupturas
// estructurales de F1 DAI por localidad, tabla `change_points`).
export function useChangePoints() {
  return useQuery({
    queryKey: queryKeys.changePoints.all,
    queryFn: async (): Promise<ChangePointRow[]> => {
      const { data, error } = await supabase.from("change_points").select("*");
      if (error) throw error;
      return data;
    },
  });
}
