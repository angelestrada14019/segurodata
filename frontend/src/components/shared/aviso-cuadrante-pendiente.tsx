export function AvisoCuadrantePendiente() {
  return (
    <div
      role="status"
      className="flex flex-col gap-2 rounded-md border border-warning/40 bg-warning/10 p-4 text-sm text-warning-foreground"
    >
      <p className="font-medium">Cuadrante pendiente de asignación</p>
      <p>
        Tu cuenta de COMANDANTE_CAI todavía no tiene un cuadrante asignado. Un
        usuario ADMIN debe asignártelo desde el panel de administración antes
        de que puedas ver predicciones y recomendaciones de tu zona.
      </p>
      <p className="text-warning-foreground/80">
        Si crees que esto es un error, contacta al administrador del sistema.
      </p>
    </div>
  );
}
