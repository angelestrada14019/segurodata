import { useState } from "react";
import { CircleAlert, Info, Lock, Minus, TrendingDown, TrendingUp } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api-client";
import { cn, formatearPeriodo } from "@/lib/utils";
import { etiquetaFeature } from "@/lib/features-modelo";
import {
  COLOR_RIESGO_HEX,
  ETIQUETA_RIESGO,
  type NivelRiesgo,
} from "@/lib/colores-riesgo";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { PanelSkeleton } from "@/components/shared/loading-states";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { ExplainResponse, PredictResponse, ShapFeatureValor } from "@/types/api";

interface TabPrediccionProps {
  prediccion: PredictResponse | undefined;
  explicacion: ExplainResponse | undefined;
  isLoading: boolean;
  error: Error | null;
}

const ORDEN_PROBABILIDADES: NivelRiesgo[] = ["CRITICO", "ALTO", "MEDIO", "BAJO"];

/**
 * Pestaña Predicción — POST /predict + GET /explain (SHAP pre-computado).
 * Resiliente a fallo parcial: si /predict responde pero /explain falla o
 * todavía carga, se muestra igual la predicción (no se bloquea la pestaña
 * completa por un solo endpoint caído).
 */
export function TabPrediccion({
  prediccion,
  explicacion,
  isLoading,
  error,
}: TabPrediccionProps) {
  if (isLoading && !prediccion) {
    return <PanelSkeleton lineas={6} />;
  }

  if (!prediccion) {
    return <EstadoErrorPrediccion error={error} />;
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4 rounded-md border border-border bg-card p-4">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">
            Período de referencia
          </p>
          <p className="font-mono-data text-sm text-foreground">
            {formatearPeriodo(prediccion.anio, prediccion.mes)}
          </p>
        </div>
        <BadgeNivelRiesgo nivelRiesgo={prediccion.nivel_riesgo} />
      </div>

      <section aria-labelledby="titulo-probabilidades" className="flex flex-col gap-3">
        <h3
          id="titulo-probabilidades"
          className="text-xs font-semibold text-muted-foreground uppercase tracking-wide"
        >
          Distribución de probabilidad por banda
        </h3>
        <BarrasProbabilidad probabilidades={prediccion.probabilidades} />
      </section>

      {explicacion ? (
        <SeccionShap explicacion={explicacion} />
      ) : (
        <div className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground">
          {isLoading
            ? "Cargando variables explicativas (SHAP)…"
            : "No se pudo cargar el detalle explicativo (SHAP) para este período."}
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Fuente del dato:{" "}
        <span className="font-mono-data">{prediccion.origen}</span>
      </p>
    </div>
  );
}

function BarrasProbabilidad({
  probabilidades,
}: {
  probabilidades: PredictResponse["probabilidades"];
}) {
  return (
    <div className="flex flex-col gap-2">
      {ORDEN_PROBABILIDADES.map((nivel) => {
        const valor = probabilidades[nivel];
        const porcentaje = Math.round(valor * 100);
        return (
          <div
            key={nivel}
            className="flex items-center gap-3"
            aria-label={`Probabilidad de nivel ${ETIQUETA_RIESGO[nivel]}: ${porcentaje}%`}
          >
            <span className="w-16 shrink-0 font-mono-data text-xs tracking-wide text-muted-foreground uppercase">
              {ETIQUETA_RIESGO[nivel]}
            </span>
            <div
              className="h-2 flex-1 overflow-hidden rounded-full bg-muted"
              aria-hidden="true"
            >
              <div
                className="h-full rounded-full"
                style={{
                  width: `${porcentaje}%`,
                  backgroundColor: COLOR_RIESGO_HEX[nivel],
                }}
              />
            </div>
            <span className="w-10 shrink-0 text-right font-mono-data text-xs text-foreground">
              {porcentaje}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

function SeccionShap({ explicacion }: { explicacion: ExplainResponse }) {
  const { rol } = useAuth();
  const [mostrarCompleto, setMostrarCompleto] = useState(false);

  const puedeVerCompleto =
    (rol === "ANALISTA_SDSCJ" || rol === "ADMIN") &&
    !!explicacion.shap_completo?.length;

  const lista =
    mostrarCompleto && explicacion.shap_completo
      ? explicacion.shap_completo
      : explicacion.shap_top3;

  return (
    <section aria-labelledby="titulo-shap" className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <h3
          id="titulo-shap"
          className="text-xs font-semibold text-muted-foreground uppercase tracking-wide"
        >
          {mostrarCompleto ? "Las 18 variables del modelo" : "Variables que más influyen"}
        </h3>
        {puedeVerCompleto && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => setMostrarCompleto((v) => !v)}
          >
            {mostrarCompleto ? "Ver solo top 3" : "Ver las 18 completas"}
          </Button>
        )}
      </div>
      <ul className="rounded-md border border-border bg-card px-4">
        {lista.map((item) => (
          <FilaShap key={item.feature} item={item} />
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        Impacto SHAP sobre el nivel de riesgo predicho — positivo (rojo)
        empuja hacia un riesgo mayor, negativo (verde) hacia uno menor.
      </p>
    </section>
  );
}

function FilaShap({ item }: { item: ShapFeatureValor }) {
  const direccion = item.valor > 0 ? "sube" : item.valor < 0 ? "baja" : "neutro";
  const Icono = direccion === "sube" ? TrendingUp : direccion === "baja" ? TrendingDown : Minus;
  const color =
    direccion === "sube"
      ? "text-destructive"
      : direccion === "baja"
        ? "text-success"
        : "text-muted-foreground";

  return (
    <li className="flex items-center justify-between gap-3 border-b border-border py-2.5 last:border-0">
      <div className="flex min-w-0 items-center gap-2">
        <Icono className={cn("h-4 w-4 shrink-0", color)} aria-hidden="true" />
        <span className="truncate text-sm text-foreground">{etiquetaFeature(item.feature)}</span>
      </div>
      <span className={cn("shrink-0 font-mono-data text-xs", color)}>
        {item.valor > 0 ? "+" : ""}
        {item.valor.toFixed(3)}
      </span>
    </li>
  );
}

function EstadoErrorPrediccion({ error }: { error: Error | null }) {
  if (!error) {
    return (
      <div
        role="status"
        className="rounded-md border border-border bg-card p-6 text-center text-sm text-muted-foreground"
      >
        Sin datos de predicción para este período.
      </div>
    );
  }

  if (error instanceof ApiError && error.status === 404) {
    return (
      <Alert>
        <Info className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Sin predicción disponible</AlertTitle>
        <AlertDescription>
          Todavía no hay una predicción calculada para esta UPZ en el período
          vigente.
        </AlertDescription>
      </Alert>
    );
  }

  if (error instanceof ApiError && error.status === 403) {
    return (
      <Alert variant="destructive">
        <Lock className="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Fuera de tu cuadrante</AlertTitle>
        <AlertDescription>
          Esta UPZ no pertenece al cuadrante asignado a tu usuario.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Alert variant="destructive">
      <CircleAlert className="h-4 w-4" aria-hidden="true" />
      <AlertTitle>No se pudo cargar la predicción</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
    </Alert>
  );
}
