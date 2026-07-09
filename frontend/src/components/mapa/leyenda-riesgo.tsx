import {
  COLOR_RIESGO_HEX,
  COLOR_SIN_DATOS_HEX,
  ETIQUETA_RIESGO,
  type NivelRiesgo,
} from "@/lib/colores-riesgo";

const ORDEN_LEYENDA: NivelRiesgo[] = ["CRITICO", "ALTO", "MEDIO", "BAJO"];

/**
 * Leyenda fija de niveles de riesgo — chips con `aria-label` describiendo
 * el nivel completo (ej. "Nivel de riesgo crítico, color morado"), porque el
 * color NUNCA puede ser el único vehículo de la información (WCAG 1.4.1).
 */
export function LeyendaRiesgo() {
  return (
    <div
      className="flex flex-col gap-1.5 rounded-md border border-border bg-card/95 p-3 font-mono-data text-xs shadow-lg backdrop-blur-sm"
      role="group"
      aria-label="Leyenda de niveles de riesgo"
    >
      <span className="mb-0.5 font-sans text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
        Nivel de riesgo
      </span>
      {ORDEN_LEYENDA.map((nivel) => (
        <div key={nivel} className="flex items-center gap-2">
          <span
            className="h-2.5 w-2.5 shrink-0 rounded-full"
            style={{ backgroundColor: COLOR_RIESGO_HEX[nivel] }}
            aria-hidden="true"
          />
          <span
            aria-label={`Nivel de riesgo ${ETIQUETA_RIESGO[nivel].toLowerCase()}, color ${nombreColorEs(nivel)}`}
          >
            {ETIQUETA_RIESGO[nivel]}
          </span>
        </div>
      ))}
      <div className="mt-1 flex items-center gap-2 border-t border-border pt-1.5">
        <span
          className="h-2.5 w-2.5 shrink-0 rounded-full"
          style={{ backgroundColor: COLOR_SIN_DATOS_HEX }}
          aria-hidden="true"
        />
        <span aria-label="Sin datos de riesgo disponibles, color gris">
          Sin datos
        </span>
      </div>
    </div>
  );
}

function nombreColorEs(nivel: NivelRiesgo): string {
  const nombres: Record<NivelRiesgo, string> = {
    CRITICO: "morado",
    ALTO: "rojo",
    MEDIO: "naranja",
    BAJO: "verde",
  };
  return nombres[nivel];
}
