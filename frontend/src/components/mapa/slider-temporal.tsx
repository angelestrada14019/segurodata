import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRangoPeriodos, type Periodo } from "@/hooks/use-rango-periodos";
import { cn } from "@/lib/utils";

interface SliderTemporalProps {
  /**
   * Período seleccionado por el usuario — `null` mientras no ha interactuado
   * con el slider todavía. A propósito NO se siembra automáticamente con
   * `rango.hasta` al montar: `mapa-riesgo.tsx` ya resuelve "período más
   * reciente" de forma interna en `useUpzGeometrias()`/
   * `useLocalidadesGeometrias()` cuando `anio`/`mes` llegan `undefined` (su
   * comportamiento original, sin cambios). Si este componente forzara ese
   * mismo valor hacia el padre como un (anio, mes) EXPLÍCITO apenas resuelve
   * el rango, dispararía una consulta con un query key nuevo/distinto y el
   * mapa se quedaría un instante sin capa base mientras esa segunda consulta
   * responde (parpadeo en cada carga). Este componente solo reporta un
   * período nuevo cuando el usuario mueve el slider — ver `ordinalActual`
   * abajo para cómo se muestra visualmente en `rango.hasta` mientras tanto.
   */
  periodo: Periodo | null;
  onCambiarPeriodo: (periodo: Periodo) => void;
  /**
   * `true` mientras el mapa trae en segundo plano el período recién
   * seleccionado (`isFetching` de la query activa en `mapa-riesgo.tsx`, no
   * `isLoading` — con `keepPreviousData` el mapa sigue mostrando el período
   * anterior durante ese lapso, así que sin esta señal el cambio de mes no
   * tenía NINGÚN indicio visual y se leía como una UI congelada).
   */
  actualizando?: boolean;
  className?: string;
}

const MESES_ES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function claveOrdinal(p: Periodo): number {
  return p.anio * 12 + (p.mes - 1);
}

function periodoDesdeOrdinal(ordinal: number): Periodo {
  return { anio: Math.floor(ordinal / 12), mes: (ordinal % 12) + 1 };
}

/**
 * Slider temporal — navega meses históricos de `predicciones` cambiando el
 * (anio, mes) que consumen `use-upz-geometrias`/`use-localidades-geometrias`
 * en `mapa-riesgo.tsx`. Rango real resuelto vía `useRangoPeriodos` (nunca
 * hardcodeado — ver ese hook para la degradación anon/RLS).
 *
 * Este componente es dueño de la resolución del rango (self-contained, igual
 * que `LeyendaRiesgo`/`IndicadorChangePoint`) y decide su posición visual por
 * defecto (`rango.hasta`, el período vigente) sin necesidad de que el padre
 * ya tenga un `periodo` explícito — ver el comentario en `SliderTemporalProps`
 * sobre por qué NO se sincroniza ese default hacia el padre automáticamente.
 */
export function SliderTemporal({
  periodo,
  onCambiarPeriodo,
  actualizando = false,
  className,
}: SliderTemporalProps) {
  const rangoQuery = useRangoPeriodos();
  const rango = rangoQuery.data;

  if (!rango) return null;

  const minOrdinal = claveOrdinal(rango.desde);
  const maxOrdinal = claveOrdinal(rango.hasta);
  if (minOrdinal >= maxOrdinal) return null; // un único período — nada que navegar

  const ordinalActual = periodo ? claveOrdinal(periodo) : maxOrdinal;
  const etiqueta = periodo
    ? `${MESES_ES[periodo.mes - 1]} ${periodo.anio}`
    : `${MESES_ES[rango.hasta.mes - 1]} ${rango.hasta.anio}`;

  function mover(delta: number) {
    const siguiente = Math.min(maxOrdinal, Math.max(minOrdinal, ordinalActual + delta));
    onCambiarPeriodo(periodoDesdeOrdinal(siguiente));
  }

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border border-border bg-card/95 px-3 py-2 shadow-lg backdrop-blur-sm",
        className,
      )}
      role="group"
      aria-label="Período consultado"
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0"
        onClick={() => mover(-1)}
        disabled={ordinalActual <= minOrdinal}
        aria-label="Mes anterior"
      >
        <ChevronLeft className="h-4 w-4" aria-hidden="true" />
      </Button>

      <div className="flex min-w-0 flex-col items-center gap-1">
        <label htmlFor="slider-temporal-input" className="sr-only">
          Período consultado
        </label>
        <input
          id="slider-temporal-input"
          type="range"
          min={minOrdinal}
          max={maxOrdinal}
          step={1}
          value={ordinalActual}
          onChange={(e) => onCambiarPeriodo(periodoDesdeOrdinal(Number(e.target.value)))}
          className="h-1.5 w-40 cursor-pointer accent-primary sm:w-56"
          aria-valuetext={etiqueta}
        />
        <span
          className="flex items-center gap-1.5 font-mono-data text-xs text-muted-foreground"
          role="status"
          aria-live="polite"
        >
          {etiqueta}
          {actualizando && (
            <>
              <Loader2 className="h-3 w-3 animate-spin text-primary" aria-hidden="true" />
              <span className="sr-only">Actualizando datos del período…</span>
            </>
          )}
        </span>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 shrink-0"
        onClick={() => mover(1)}
        disabled={ordinalActual >= maxOrdinal}
        aria-label="Mes siguiente"
      >
        <ChevronRight className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  );
}
