import { TrendingDown, TrendingUp, Waves } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChangePoints } from "@/hooks/use-change-points";
import type { ChangePointRow, TipoCambio } from "@/types/supabase";

interface IndicadorChangePointProps {
  /** `cod_localidad` de la UPZ seleccionada — `change_points` está indexada
   * por localidad (ruptures corre sobre F1 DAI agregado por localidad, no
   * por UPZ, ver `scripts/compute_change_points.py`), nunca por `upz_cod`. */
  codLocalidad: string | null | undefined;
  className?: string;
}

/** Una ruptura de hace muchos años ya no es contexto operativo relevante
 * para el diagnóstico vigente — solo se muestra si cae dentro de esta
 * ventana de años respecto al año actual. */
const VENTANA_RECIENCIA_ANIOS = 3;

const ESTILO_POR_TIPO: Record<TipoCambio, string> = {
  ALZA: "border-destructive/40 bg-destructive/10 text-destructive",
  BAJA: "border-success/40 bg-success/10 text-success",
  INDEFINIDO: "border-warning/40 bg-warning/10 text-warning",
};

const ICONO_POR_TIPO: Record<TipoCambio, typeof TrendingUp> = {
  ALZA: TrendingUp,
  BAJA: TrendingDown,
  INDEFINIDO: Waves,
};

const ETIQUETA_POR_TIPO: Record<TipoCambio, string> = {
  ALZA: "Cambio estructural — alza sostenida",
  BAJA: "Cambio estructural — baja sostenida",
  INDEFINIDO: "Cambio estructural detectado",
};

/**
 * Badge "cambio estructural" — distingue una ruptura detectada por
 * `ruptures` (PELT sobre el histórico DAI 2018–2026 de F1, tabla
 * `change_points`) de una simple fluctuación temporal/estacional. Da
 * contexto causal antes de leer el diagnóstico por variable: si la
 * localidad tuvo un quiebre estructural reciente, la causa dominante del
 * riesgo probablemente no es coyuntural.
 *
 * Si no hay ningún change point reciente para la localidad, no renderiza
 * nada — nunca se inventa un estado "sin cambios" (instrucción explícita).
 */
export function IndicadorChangePoint({ codLocalidad, className }: IndicadorChangePointProps) {
  const { data: changePoints } = useChangePoints();

  const masReciente = seleccionarChangePointReciente(changePoints, codLocalidad);

  if (!masReciente) {
    return null;
  }

  const Icono = ICONO_POR_TIPO[masReciente.tipo_cambio];
  const anio = masReciente.fecha_ruptura.slice(0, 4);
  const magnitudTexto = formatearMagnitud(masReciente.magnitude);

  return (
    <div
      role="status"
      className={cn(
        "flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border px-3 py-2 text-sm",
        ESTILO_POR_TIPO[masReciente.tipo_cambio],
        className,
      )}
    >
      <Icono className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="font-medium">{ETIQUETA_POR_TIPO[masReciente.tipo_cambio]}</span>
      <span className="font-mono-data text-xs opacity-90">
        {masReciente.localidad_nom ?? codLocalidad} · {anio}
        {magnitudTexto ? ` · ${magnitudTexto}` : ""}
      </span>
    </div>
  );
}

function seleccionarChangePointReciente(
  changePoints: ChangePointRow[] | undefined,
  codLocalidad: string | null | undefined,
): ChangePointRow | null {
  if (!changePoints || !codLocalidad) return null;

  const anioActual = new Date().getFullYear();
  // `fecha_ruptura` es "YYYY-01-01" — se lee el año como substring en vez de
  // `new Date(...).getFullYear()` para evitar el corrimiento de un año que
  // produce parsear una fecha UTC-medianoche en una zona horaria negativa
  // (Bogotá es UTC-5).
  const candidatos = changePoints.filter((cp) => {
    if (cp.localidad_cod !== codLocalidad) return false;
    const anioRuptura = Number(cp.fecha_ruptura.slice(0, 4));
    return anioActual - anioRuptura <= VENTANA_RECIENCIA_ANIOS;
  });

  if (candidatos.length === 0) return null;

  return candidatos.reduce((masReciente, actual) =>
    actual.fecha_ruptura > masReciente.fecha_ruptura ? actual : masReciente,
  );
}

function formatearMagnitud(magnitude: number | null | undefined): string | null {
  if (magnitude === null || magnitude === undefined) return null;
  const porcentaje = Math.round(magnitude * 100);
  return `${porcentaje > 0 ? "+" : ""}${porcentaje}%`;
}
