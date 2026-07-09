import { useEffect } from "react";
import { supabase } from "@/lib/supabase";

// TODO(Sprint 2): suscripción Realtime a `silver_upz_mes` para el Módulo 1
// (actualizaciones en vivo del diagnóstico). Patrón: skill supabase-segurodata,
// sección "Conexión desde React".
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
