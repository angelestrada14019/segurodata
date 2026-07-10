import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";
import { queryKeys } from "@/lib/query-keys";
import type { UserProfileRow } from "@/types/supabase";

/**
 * Lista completa de perfiles (`user_profiles`) — Panel Admin
 * (`/admin/usuarios`, rol ADMIN únicamente vía `ProtectedRoute`). Lectura
 * 100% Supabase directa: la política RLS `perfil_propio_o_admin`
 * (`supabase/migrations/20260610_0008_advisor_fixes.sql`, fusiona
 * `perfil_propio`+`admin_lee_perfiles` de la migración 0006) ya deja leer
 * TODAS las filas a un usuario con `rol=ADMIN` en el JWT — no existe (ni
 * hace falta) un endpoint FastAPI para listar usuarios.
 *
 * Query key `queryKeys.adminUsuarios.all` — a propósito la MISMA que usa
 * `hooks/use-admin-asignar-cuadrante.ts` en su `onSuccess`: tras asignar o
 * reasignar un cuadrante esta lista se invalida y refetchea sola, sin
 * cableado adicional en `routes/admin-usuarios.tsx`.
 */
export function useUsuarios() {
  return useQuery({
    queryKey: queryKeys.adminUsuarios.all,
    queryFn: async (): Promise<UserProfileRow[]> => {
      const { data, error } = await supabase
        .from("user_profiles")
        .select("*")
        .order("created_at", { ascending: false });
      if (error) throw error;
      return data;
    },
  });
}
