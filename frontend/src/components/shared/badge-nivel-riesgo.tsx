import { cn } from "@/lib/utils";
import {
  ETIQUETA_RIESGO,
  esNivelRiesgo,
  type NivelRiesgo,
} from "@/lib/colores-riesgo";

interface BadgeNivelRiesgoProps {
  nivelRiesgo: NivelRiesgo | string | null | undefined;
  className?: string;
}

const ESTILOS_POR_NIVEL: Record<NivelRiesgo, string> = {
  CRITICO: "bg-riesgo-critico/15 text-riesgo-critico border-riesgo-critico/40",
  ALTO: "bg-riesgo-alto/15 text-riesgo-alto border-riesgo-alto/40",
  MEDIO: "bg-riesgo-medio/15 text-riesgo-medio border-riesgo-medio/40",
  BAJO: "bg-riesgo-bajo/15 text-riesgo-bajo border-riesgo-bajo/40",
};

/**
 * ÚNICO componente que traduce `nivel_riesgo` a color/texto en HTML (el mapa
 * deck.gl usa `lib/colores-riesgo.ts` directo). Cualquier otra parte de la UI
 * que necesite mostrar un nivel de riesgo debe usar este componente — nunca
 * repetir la lógica de color/etiqueta en otro archivo.
 */
export function BadgeNivelRiesgo({
  nivelRiesgo,
  className,
}: BadgeNivelRiesgoProps) {
  if (!esNivelRiesgo(nivelRiesgo)) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-sm border border-riesgo-sin-datos/40 bg-riesgo-sin-datos/15 px-2 py-0.5 font-mono-data text-xs font-medium tracking-wide text-riesgo-sin-datos uppercase",
          className,
        )}
        aria-label="Sin datos de riesgo para este período"
      >
        Sin datos
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 font-mono-data text-xs font-medium tracking-wide uppercase",
        ESTILOS_POR_NIVEL[nivelRiesgo],
        className,
      )}
      aria-label={`Nivel de riesgo ${ETIQUETA_RIESGO[nivelRiesgo].toLowerCase()}`}
    >
      <span
        className="h-1.5 w-1.5 rounded-full bg-current"
        aria-hidden="true"
      />
      {ETIQUETA_RIESGO[nivelRiesgo]}
    </span>
  );
}
