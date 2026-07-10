import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";
import { PanelSkeleton } from "@/components/shared/loading-states";
import type { RolBackend } from "@/types/api";

interface ProtectedRouteProps {
  children: ReactNode;
  /** Roles con acceso a esta ruta. Omitir = cualquier sesión autenticada basta. */
  rolesPermitidos?: RolBackend[];
}

/**
 * Wrapper de rutas: sesión + rol + chequeo cuadrante_pendiente.
 * - `loading` → pantalla de carga (skeleton, no spinner genérico).
 * - sin sesión → redirige a `/login?next=<path>`.
 * - rol fuera de `rolesPermitidos` → redirige a `/no-autorizado`.
 * - COMANDANTE_CAI sin cuadrante asignado → redirige a `/cuadrante-pendiente`
 *   (excepto si la ruta destino YA es esa, para no crear un loop).
 */
export function ProtectedRoute({
  children,
  rolesPermitidos,
}: ProtectedRouteProps) {
  const { session, rol, cuadrantePendiente, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="p-6">
        <PanelSkeleton lineas={3} />
      </div>
    );
  }

  if (!session) {
    const next = encodeURIComponent(location.pathname);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  if (rolesPermitidos && (!rol || !rolesPermitidos.includes(rol))) {
    return <Navigate to="/no-autorizado" replace />;
  }

  if (cuadrantePendiente && location.pathname !== "/cuadrante-pendiente") {
    return <Navigate to="/cuadrante-pendiente" replace />;
  }

  return <>{children}</>;
}
