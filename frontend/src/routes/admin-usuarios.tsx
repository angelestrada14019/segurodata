import { useState } from "react";
import { CircleAlert } from "lucide-react";
import { useUsuarios } from "@/hooks/use-usuarios";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { TablaUsuarios } from "@/components/admin/tabla-usuarios";
import { DialogAsignarCuadrante } from "@/components/admin/dialog-asignar-cuadrante";
import type { UserProfileRow } from "@/types/supabase";

/**
 * Panel Admin — gestión de usuarios (`/admin/usuarios`, rol ADMIN
 * únicamente, ya filtrado por `ProtectedRoute` en App.tsx). 100% Supabase
 * directo: no existe un endpoint FastAPI para listar `user_profiles` — la
 * política RLS `perfil_propio_o_admin` ya le deja leer todas las filas a un
 * ADMIN (ver `hooks/use-usuarios.ts`). El único endpoint del backend que
 * toca esta vista es PATCH /admin/usuarios/{id}/cuadrante, disparado desde
 * `components/admin/dialog-asignar-cuadrante.tsx`.
 */
export function AdminUsuariosPage() {
  const { data: usuarios, isLoading, isError, error } = useUsuarios();

  // Patrón "sticky": el usuario elegido se conserva mientras Radix anima el
  // cierre del Dialog (mismo criterio que `upzModalCod`/`modalAbierto` en
  // `components/mapa/mapa-riesgo.tsx`) — evita que el contenido del Dialog
  // se vacíe a mitad de la animación de cierre.
  const [usuarioDialogo, setUsuarioDialogo] = useState<UserProfileRow | null>(
    null,
  );
  const [dialogoAbierto, setDialogoAbierto] = useState(false);

  function abrirDialogoAsignar(usuario: UserProfileRow) {
    setUsuarioDialogo(usuario);
    setDialogoAbierto(true);
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
          Administración de usuarios
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Perfiles registrados en SeguroData — asigna el cuadrante de cada
          Comandante CAI para habilitar sus predicciones filtradas por RLS.
        </p>
      </div>

      {isError ? (
        <Alert variant="destructive">
          <CircleAlert className="h-4 w-4" aria-hidden="true" />
          <AlertTitle>No se pudo cargar la lista de usuarios</AlertTitle>
          <AlertDescription>
            {error instanceof Error
              ? error.message
              : "Intenta recargar la página."}
          </AlertDescription>
        </Alert>
      ) : (
        <TablaUsuarios
          usuarios={usuarios}
          isLoading={isLoading}
          onAsignarCuadrante={abrirDialogoAsignar}
        />
      )}

      {usuarioDialogo && (
        <DialogAsignarCuadrante
          usuario={usuarioDialogo}
          open={dialogoAbierto}
          onOpenChange={setDialogoAbierto}
        />
      )}
    </div>
  );
}
