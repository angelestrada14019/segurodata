import { useEffect, useRef, useState } from "react";
import { CircleAlert, Info, Loader2, Lock, RefreshCw, Sparkles } from "lucide-react";
import { useDiagnosticoUpz } from "@/hooks/use-diagnostico-upz";
import { usePrescribe } from "@/hooks/use-prescribe";
import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { ApiError } from "@/lib/api-client";
import { formatearPeriodo } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { PanelSkeleton } from "@/components/shared/loading-states";
import { SelectorUpz } from "@/components/prescriptivo/selector-upz";
import { IndicadorChangePoint } from "@/components/prescriptivo/indicador-change-point";
import { PanelCai } from "@/components/prescriptivo/panel-cai";
import { TablaOntologica } from "@/components/prescriptivo/tabla-ontologica";
import type { PredictResponse, ShapFeatureValor } from "@/types/api";

/**
 * Módulo 3 — Prescriptivo, vista standalone. A diferencia de la pestaña
 * Sugerencia del modal UPZ (que depende de haber hecho click en el mapa),
 * esta página trae su propio selector de UPZ (`SelectorUpz`) y resuelve el
 * mismo flujo predict→explain→prescribe de forma independiente — reusa
 * `useDiagnosticoUpz` (mismo hook que consume el modal) para el período
 * vigente + SHAP top-3, y dispara POST /prescribe de forma MANUAL (botón),
 * igual que `tab-sugerencia.tsx`: es una llamada con costo de LLM, no un GET
 * idempotente.
 *
 * Roles con acceso: COMANDANTE_CAI · ANALISTA_SDSCJ · ADMIN — ya filtrados
 * por `ProtectedRoute` en App.tsx antes de que este componente monte, así
 * que no repite el chequeo de rol aquí (a diferencia de `tab-sugerencia.tsx`,
 * que vive dentro del modal accesible desde /diagnostico, ruta pública).
 */
export function ModuloPrescriptivoPage() {
  const [upzCod, setUpzCod] = useState<string | undefined>(undefined);

  const upzGeometriasQuery = useUpzGeometrias();
  const upzFeature = upzGeometriasQuery.data?.features.find(
    (f) => f.properties.upz_cod === upzCod,
  );

  const {
    prediccion,
    explicacion,
    isLoading: prediccionCargando,
    error: prediccionError,
  } = useDiagnosticoUpz(upzCod ?? "", !!upzCod);

  const prescribeMutation = usePrescribe();

  // Mismo patrón que `modal-upz.tsx` para el reset de `graphragMutation`:
  // `prescribeMutation` es un objeto nuevo en cada render (useMutation), así
  // que el efecto solo debe reaccionar a cambios de `upzCod` — nunca a la
  // identidad de ese objeto (si entrara completo en deps, la mutación se
  // reiniciaría en CADA render, no solo al cambiar de UPZ). Sin este reset,
  // cambiar de UPZ después de generar una recomendación dejaría en pantalla
  // el CAI/diagnóstico de la UPZ anterior hasta el próximo click en
  // "Generar".
  const prescribeMutationRef = useRef(prescribeMutation);
  prescribeMutationRef.current = prescribeMutation;

  useEffect(() => {
    prescribeMutationRef.current.reset();
  }, [upzCod]);

  const shapTop = explicacion?.shap_top3;

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
          Módulo 3 — Prescriptivo
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Diagnóstico causal y recomendación operacional por UPZ — a qué
          cuadrante avisar y por qué.
        </p>
      </div>

      <SelectorUpz value={upzCod} onValueChange={setUpzCod} />

      {!upzCod ? (
        <div
          role="status"
          className="rounded-md border border-dashed border-border p-8 text-center text-sm text-muted-foreground"
        >
          Selecciona una UPZ para ver su diagnóstico prescriptivo.
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          <ContextoUpz
            upzCod={upzCod}
            nombreUpz={upzFeature?.properties.upz_nombre}
            nomLocalidad={upzFeature?.properties.nom_localidad}
            prediccion={prediccion}
            isLoading={prediccionCargando}
            error={prediccionError}
          />

          <IndicadorChangePoint codLocalidad={upzFeature?.properties.cod_localidad} />

          {prediccion &&
            (shapTop && shapTop.length > 0 ? (
              <SeccionResultado upzCod={upzCod} shapTop={shapTop} mutation={prescribeMutation} />
            ) : (
              <div
                role="status"
                className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground"
              >
                {prediccionCargando
                  ? "Cargando variables explicativas (SHAP)…"
                  : "No se pudo cargar el detalle explicativo (SHAP) para este período — no es posible generar una recomendación todavía."}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

interface ContextoUpzProps {
  upzCod: string;
  nombreUpz: string | undefined;
  nomLocalidad: string | null | undefined;
  prediccion: PredictResponse | undefined;
  isLoading: boolean;
  error: Error | null;
}

/** Ficha compacta de la UPZ elegida — nombre, localidad, período vigente y
 * nivel de riesgo. Da el contexto mínimo antes de pedir una recomendación;
 * el detalle completo de probabilidades/SHAP vive en el Módulo 2. */
function ContextoUpz({
  upzCod,
  nombreUpz,
  nomLocalidad,
  prediccion,
  isLoading,
  error,
}: ContextoUpzProps) {
  if (isLoading && !prediccion) {
    return <PanelSkeleton lineas={2} />;
  }

  if (!prediccion) {
    if (error instanceof ApiError && error.status === 404) {
      return (
        <Alert>
          <Info className="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Sin predicción disponible</AlertTitle>
          <AlertDescription>
            Todavía no hay una predicción calculada para esta UPZ en el
            período vigente — no es posible generar una recomendación.
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
        <AlertDescription>
          {error?.message ?? "Intenta con otra UPZ."}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-border bg-card p-4">
      <div>
        <h2 className="text-base font-semibold text-foreground">
          {nombreUpz ?? `UPZ ${upzCod}`}
        </h2>
        <p className="font-mono-data text-xs text-muted-foreground">
          {upzCod}
          {nomLocalidad ? ` · ${nomLocalidad}` : ""} ·{" "}
          {formatearPeriodo(prediccion.anio, prediccion.mes)}
        </p>
      </div>
      <BadgeNivelRiesgo nivelRiesgo={prediccion.nivel_riesgo} />
    </div>
  );
}

interface SeccionResultadoProps {
  upzCod: string;
  shapTop: ShapFeatureValor[];
  mutation: ReturnType<typeof usePrescribe>;
}

/** Estado de la llamada POST /prescribe — pending/error/idle/data. Mismo
 * flujo visual que `tab-sugerencia.tsx` (mismo backend, mismo contrato),
 * pero sin compartir código: esta página no depende de un click previo en
 * el mapa ni del ciclo de vida de las pestañas del modal, así que dueña de
 * su propio disparo manual. Lo compartido de verdad (bloque CAI y tabla
 * ontológica) ya está extraído en `components/prescriptivo/`. */
function SeccionResultado({ upzCod, shapTop, mutation }: SeccionResultadoProps) {
  function generar() {
    mutation.mutate({ upz_cod: upzCod, shap_top: shapTop });
  }

  if (mutation.isPending) {
    return (
      <div
        role="status"
        className="flex flex-col items-center gap-3 rounded-md border border-border bg-card p-8 text-center"
      >
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">
          Analizando causas y generando recomendación…
        </p>
      </div>
    );
  }

  if (mutation.isError) {
    const mensaje =
      mutation.error instanceof ApiError && mutation.error.status === 403
        ? "Tu rol no tiene permiso para generar recomendaciones."
        : (mutation.error?.message ?? "No se pudo generar la recomendación.");

    return (
      <div className="flex flex-col gap-3">
        <Alert variant="destructive">
          <AlertTitle>No se pudo generar la recomendación</AlertTitle>
          <AlertDescription>{mensaje}</AlertDescription>
        </Alert>
        <Button type="button" variant="outline" onClick={generar} className="w-fit">
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Reintentar
        </Button>
      </div>
    );
  }

  if (!mutation.data) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
        <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" />
        <p className="max-w-sm text-sm text-muted-foreground">
          Genera el diagnóstico causal y la recomendación operacional para
          esta UPZ a partir de las variables que más influyen en su riesgo.
        </p>
        <Button type="button" onClick={generar}>
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          Generar recomendación
        </Button>
      </div>
    );
  }

  const data = mutation.data;

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-md border border-primary/40 bg-primary/5 p-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold tracking-wide text-primary uppercase">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          Recomendación operacional
        </div>
        <p className="text-sm leading-relaxed text-foreground">{data.recomendacion_llm}</p>
      </div>

      <PanelCai cai={data.cai} />

      <TablaOntologica diagnosticos={data.diagnosticos} />

      <Button type="button" variant="outline" size="sm" onClick={generar} className="w-fit">
        <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
        Regenerar recomendación
      </Button>
    </div>
  );
}
