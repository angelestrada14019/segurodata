// TODO(Sprint 2): consumir FastAPI /predict + /explain. Roles con acceso:
// COMANDANTE_CAI (solo su cuadrante) · ANALISTA_SDSCJ · ADMIN.
// CIUDADANO NO tiene acceso a este módulo (restricción real, ver navbar.tsx).
export function ModuloPrediccionPage() {
  return (
    <div className="p-6">
      <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
        Módulo 2 — Predicción
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Disponible en Sprint 2.
      </p>
    </div>
  );
}
