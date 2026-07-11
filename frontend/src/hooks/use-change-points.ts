import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { ChangePointRow } from "@/types/supabase";

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
