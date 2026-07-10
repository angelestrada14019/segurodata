import { Layers } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { DISPONIBLE as CAMARAS_DISPONIBLE } from "@/components/mapa/capa-camaras";
import { DISPONIBLE as ALUMBRADO_DISPONIBLE } from "@/components/mapa/capa-alumbrado";
import { DISPONIBLE as TM_DISPONIBLE } from "@/components/mapa/capa-transmilenio";

/** Capas reales controladas por este panel — entran/salen del array `layers`
 * de `mapa-riesgo.tsx` según estos booleanos (estado controlado, el padre es
 * dueño de `capas`). */
export interface CapasVisibles {
  cuadrantes: boolean;
  rupturas: boolean;
}

interface PanelCapasProps {
  capas: CapasVisibles;
  onCambiarCapas: (capas: CapasVisibles) => void;
  className?: string;
}

const CAPAS_DISPONIBLES: { id: keyof CapasVisibles; etiqueta: string }[] = [
  { id: "cuadrantes", etiqueta: "Cuadrantes de Policía" },
  { id: "rupturas", etiqueta: "Cambios estructurales" },
];

/** Wireado a la constante `DISPONIBLE` que exporta cada `capa-*.tsx` — si
 * algún día una de estas fuentes deja de ser placeholder=0 en el modelo
 * (ver `CLAUDE.md` raíz), basta con flipear esa constante para que el
 * checkbox salga de esta lista, sin mantener un segundo listado a mano. */
const CAPAS_PENDIENTES: { etiqueta: string; disponible: boolean }[] = [
  { etiqueta: "Cámaras Salvavidas (F13)", disponible: CAMARAS_DISPONIBLE },
  { etiqueta: "Alumbrado público (F14)", disponible: ALUMBRADO_DISPONIBLE },
  { etiqueta: "Estaciones TransMilenio", disponible: TM_DISPONIBLE },
];

/**
 * Panel de capas toggleables del mapa — controla qué factories de
 * `capa-*.tsx` entran al array `layers` de `mapa-riesgo.tsx`. Cámaras
 * F13/Alumbrado F14/TransMilenio se listan DESHABILITADAS a propósito: el
 * placeholder=0 de esas 3 features en el modelo (`CLAUDE.md` raíz) significa
 * que no hay geometría real que dibujar todavía — mostrarlas como checkbox
 * inactivo con "Pendiente de datos" documenta el roadmap sin inventar datos.
 */
export function PanelCapas({ capas, onCambiarCapas, className }: PanelCapasProps) {
  return (
    <div
      className={cn(
        "flex w-56 flex-col gap-2 rounded-md border border-border bg-card/95 p-3 text-xs shadow-lg backdrop-blur-sm",
        className,
      )}
      role="group"
      aria-label="Capas del mapa"
    >
      <div className="mb-0.5 flex items-center gap-1.5 font-sans text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
        <Layers className="h-3.5 w-3.5" aria-hidden="true" />
        Capas
      </div>

      {CAPAS_DISPONIBLES.map((opcion) => (
        <div key={opcion.id} className="flex items-center gap-2">
          <Checkbox
            id={`capa-${opcion.id}`}
            checked={capas[opcion.id]}
            onCheckedChange={(marcado) =>
              onCambiarCapas({ ...capas, [opcion.id]: marcado === true })
            }
          />
          <Label htmlFor={`capa-${opcion.id}`} className="cursor-pointer font-normal">
            {opcion.etiqueta}
          </Label>
        </div>
      ))}

      <div className="mt-1 flex flex-col gap-1 border-t border-border pt-1.5 text-muted-foreground">
        {CAPAS_PENDIENTES.filter((c) => !c.disponible).map((c) => (
          <div key={c.etiqueta} className="flex items-center gap-2">
            <Checkbox checked={false} disabled aria-label={`${c.etiqueta} — pendiente de datos`} />
            <span>
              {c.etiqueta}
              <span className="ml-1 italic">— Pendiente de datos</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
