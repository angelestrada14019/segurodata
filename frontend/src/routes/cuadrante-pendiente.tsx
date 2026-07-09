import { AvisoCuadrantePendiente } from "@/components/shared/aviso-cuadrante-pendiente";

// TODO(Sprint 2): contenido real de esta página + redirección automática
// cuando `useAuth().cuadrantePendiente === true`.
export function CuadrantePendientePage() {
  return (
    <div className="mx-auto max-w-lg p-6">
      <AvisoCuadrantePendiente />
    </div>
  );
}
