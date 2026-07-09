import { Link } from "react-router-dom";
import { ShieldOff } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Vista mostrada por `ProtectedRoute` cuando el rol del usuario no está
 * en la lista de roles permitidos para la ruta solicitada. */
export function NoAutorizadoPage() {
  return (
    <div
      role="alert"
      className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center"
    >
      <ShieldOff className="h-10 w-10 text-muted-foreground" aria-hidden="true" />
      <h1 className="font-mono-data text-lg font-semibold tracking-wide">
        Acceso no autorizado
      </h1>
      <p className="max-w-md text-sm text-muted-foreground">
        Tu rol actual no tiene permiso para ver esta sección del dashboard.
      </p>
      <Button asChild variant="outline">
        <Link to="/diagnostico">Volver al diagnóstico</Link>
      </Button>
    </div>
  );
}
