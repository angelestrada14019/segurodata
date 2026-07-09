import { createContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { useWhoami } from "@/hooks/use-whoami";
import type { RolBackend } from "@/types/api";

export interface AuthContextValue {
  /** Sesión de Supabase Auth — null si no hay usuario logueado. */
  session: Session | null;
  /** Rol resuelto por GET /whoami — undefined mientras carga o sin sesión. */
  rol: RolBackend | undefined;
  cuadranteAsignado: string | null | undefined;
  /** true cuando rol=COMANDANTE_CAI sin cuadrante_asignado (Sprint 2 redirige). */
  cuadrantePendiente: boolean;
  /**
   * true mientras se resuelve la sesión inicial de Supabase Auth O mientras
   * /whoami está en vuelo para una sesión ya detectada. `ProtectedRoute`
   * debe esperar a que esto sea false antes de decidir redirigir.
   */
  loading: boolean;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined,
);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setSessionLoading(false);
    });

    const { data: subscription } = supabase.auth.onAuthStateChange(
      (_event, nuevaSesion) => {
        setSession(nuevaSesion);
        setSessionLoading(false);
      },
    );

    return () => subscription.subscription.unsubscribe();
  }, []);

  const {
    data: whoami,
    isLoading: whoamiLoading,
    isFetching: whoamiFetching,
  } = useWhoami(!!session);

  const value = useMemo<AuthContextValue>(() => {
    const cuadrantePendiente =
      whoami?.rol === "COMANDANTE_CAI" && whoami.cuadrante_asignado === null;

    return {
      session,
      rol: whoami?.rol,
      cuadranteAsignado: whoami?.cuadrante_asignado,
      cuadrantePendiente,
      loading:
        sessionLoading || (!!session && whoamiLoading && whoamiFetching),
    };
  }, [session, sessionLoading, whoami, whoamiLoading, whoamiFetching]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
