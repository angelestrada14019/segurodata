import { useEffect } from "react";
import { supabase } from "@/lib/supabase";

export function useSilverRealtime(upzCod: string, onInsert: (payload: unknown) => void) {
  useEffect(() => {
    const channel = supabase
      .channel(`silver-upz-${upzCod}`)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "silver_upz_mes", filter: `upz_cod=eq.${upzCod}` },
        onInsert,
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [upzCod, onInsert]);
}
