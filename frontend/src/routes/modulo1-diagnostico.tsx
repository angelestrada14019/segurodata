import { ErrorBoundary } from "@/components/shared/error-boundary";
import { MapaRiesgo } from "@/components/mapa/mapa-riesgo";

/**
 * Módulo 1 — Diagnóstico. ÚNICA ruta pública (sin ProtectedRoute) del
 * dashboard. Fuente de datos: Supabase directo vía RPCs GeoJSON
 * (`upz_geojson`/`localidades_geojson`, migración 0012).
 */
export function ModuloDiagnosticoPage() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-border bg-card px-4 py-3">
        <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
          Módulo 1 — Diagnóstico
        </h1>
        <p className="text-sm text-muted-foreground">
          Nivel de riesgo actual por UPZ. Acceso público de solo lectura.
        </p>
      </div>
      <div className="relative flex min-h-[600px] flex-1">
        <ErrorBoundary>
          <MapaRiesgo />
        </ErrorBoundary>
      </div>
    </div>
  );
}
