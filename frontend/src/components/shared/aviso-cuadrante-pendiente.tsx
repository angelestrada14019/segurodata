// TODO(Sprint 2): aviso real cuando `cuadrantePendiente === true` (rol
// COMANDANTE_CAI sin cuadrante_asignado) — reemplaza el mapa vacío por un
// mensaje operacional + redirección. Ver `useAuth().cuadrantePendiente` y
// contrato GET /whoami en skill backend-segurodata.
export function AvisoCuadrantePendiente() {
  return (
    <div
      role="status"
      className="rounded-md border border-warning/40 bg-warning/10 p-4 text-sm text-warning-foreground"
    >
      Tu cuadrante aún no ha sido asignado por un administrador. Esta vista se
      completará en el próximo sprint.
    </div>
  );
}
