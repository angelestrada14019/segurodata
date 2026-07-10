import { ErrorBoundary } from "@/components/shared/error-boundary";
import { MapaRiesgo } from "@/components/mapa/mapa-riesgo";
import { Top10Riesgo } from "@/components/prediccion/top10-riesgo";

/**
 * Módulo 2 — Predicción. Roles con acceso: COMANDANTE_CAI (solo su
 * cuadrante) · ANALISTA_SDSCJ · ADMIN — ya filtrados por `ProtectedRoute` en
 * App.tsx (CIUDADANO no ve este módulo, restricción real de negocio, ver
 * `navbar.tsx`).
 *
 * `nivel_riesgo` aquí es el MISMO dato que pinta el mapa de Módulo 1 — mismo
 * lookup por PK (upz_cod, anio, mes) contra la tabla `predicciones`
 * (`backend/app/repositories/predictions_repo.py` para POST /predict, RPC
 * `upz_geojson` para el mapa), solo por dos caminos distintos. Por eso esta
 * página REUSA `<MapaRiesgo>` tal cual (cero segunda paleta, cero segunda
 * capa GeoJSON) — el valor añadido real de este módulo es el
 * `<Top10Riesgo>` y ser un segundo punto de entrada al modal ya construido,
 * abriendo directo en la pestaña "prediccion" en vez de "descripcion".
 */
export function ModuloPrediccionPage() {
  return (
    <div className="flex flex-1 flex-col">
      <div className="border-b border-border bg-card px-4 py-3">
        <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
          Módulo 2 — Predicción
        </h1>
        <p className="text-sm text-muted-foreground">
          Nivel de riesgo del período vigente por UPZ y ranking de las zonas
          de mayor riesgo.
        </p>
      </div>

      <div className="flex min-h-[600px] flex-1 flex-col lg:flex-row">
        <div className="relative flex flex-1">
          <ErrorBoundary>
            <MapaRiesgo tabInicialModal="prediccion" />
          </ErrorBoundary>
        </div>

        <aside className="flex w-full flex-col gap-3 border-t border-border bg-card/30 p-4 lg:w-[420px] lg:shrink-0 lg:overflow-y-auto lg:border-t-0 lg:border-l">
          <Top10Riesgo />
        </aside>
      </div>
    </div>
  );
}
