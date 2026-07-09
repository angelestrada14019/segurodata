import { cn } from "@/lib/utils";

/**
 * Skeletons de carga — el dashboard NUNCA usa un spinner genérico centrado
 * (rompe la sensación de "consola operacional densa"). Cada skeleton imita
 * las dimensiones finales del contenido real para evitar layout shift.
 */

function PulseBlock({ className }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse rounded-sm bg-muted", className)}
      aria-hidden="true"
    />
  );
}

/** Skeleton del mapa mientras cargan las geometrías UPZ/localidades. */
export function MapaSkeleton() {
  return (
    <div
      className="relative h-full w-full overflow-hidden bg-card"
      role="status"
      aria-label="Cargando mapa de riesgo"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,color-mix(in_oklch,var(--muted)_60%,transparent),transparent_70%)]" />
      <div className="absolute top-4 left-4 flex flex-col gap-2">
        <PulseBlock className="h-6 w-40" />
        <PulseBlock className="h-4 w-56" />
      </div>
      <div className="absolute right-4 bottom-4 flex gap-2">
        <PulseBlock className="h-8 w-20" />
        <PulseBlock className="h-8 w-20" />
        <PulseBlock className="h-8 w-20" />
        <PulseBlock className="h-8 w-20" />
      </div>
      <span className="sr-only">Cargando mapa de riesgo por UPZ</span>
    </div>
  );
}

/** Skeleton genérico para tarjetas/paneles de datos (SHAP, prescriptivo, etc). */
export function PanelSkeleton({ lineas = 4 }: { lineas?: number }) {
  return (
    <div
      className="flex flex-col gap-3 rounded-md border border-border bg-card p-4"
      role="status"
      aria-label="Cargando datos"
    >
      <PulseBlock className="h-5 w-1/3" />
      {Array.from({ length: lineas }).map((_, i) => (
        <PulseBlock key={i} className="h-4 w-full" />
      ))}
      <span className="sr-only">Cargando datos</span>
    </div>
  );
}

/** Skeleton de fila de tabla (para listas de UPZs, usuarios admin, etc). */
export function FilaTablaSkeleton({ columnas = 4 }: { columnas?: number }) {
  return (
    <tr role="status" aria-label="Cargando fila">
      {Array.from({ length: columnas }).map((_, i) => (
        <td key={i} className="p-3">
          <PulseBlock className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}
