import { Layers, Lock } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

/** Capas reales controladas por este panel — entran/salen del array `layers`
 * de `mapa-riesgo.tsx` según estos booleanos (estado controlado, el padre es
 * dueño de `capas`). */
export interface CapasVisibles {
  cuadrantes: boolean;
  rupturas: boolean;
  transmilenio: boolean;
  camaras: boolean;
  alumbrado: boolean;
}

interface PanelCapasProps {
  capas: CapasVisibles;
  onCambiarCapas: (capas: CapasVisibles) => void;
  className?: string;
}

const CAPAS_DISPONIBLES: { id: keyof CapasVisibles; etiqueta: string; requiereSesion?: boolean }[] = [
  { id: "cuadrantes", etiqueta: "Cuadrantes de Policía", requiereSesion: true },
  { id: "rupturas", etiqueta: "Cambios estructurales" },
  { id: "transmilenio", etiqueta: "Estaciones TransMilenio" },
  { id: "camaras", etiqueta: "Cámaras Salvavidas (F13)" },
  { id: "alumbrado", etiqueta: "Alumbrado público (F14)" },
];

/**
 * Panel de capas toggleables del mapa — controla qué factories de
 * `capa-*.tsx` entran al array `layers` de `mapa-riesgo.tsx`. Las 5 capas
 * tienen geometría real desde el 10-jul (F8/F13/F14 dejaron de ser
 * placeholder — ver `capa-transmilenio.tsx`/`capa-camaras.tsx`/
 * `capa-alumbrado.tsx`); si en el futuro se agrega una fuente nueva sin
 * extractor todavía, listarla aquí solo cuando exista geometría real que
 * dibujar (nunca inventar datos).
 *
 * `cuadrantes_geojson` es la única RPC que sigue siendo `authenticated`-only
 * (migración 0012, expone nombre de CAI + teléfono — decisión deliberada,
 * no un pendiente). Para un visitante sin sesión, marcar ese checkbox no
 * dispara la consulta (`mapa-riesgo.tsx`) y antes no mostraba nada sin
 * explicación — el candado + "requiere sesión" aquí cierra ese hueco con el
 * mismo criterio que ya usan `tab-prediccion.tsx`/`tab-sugerencia.tsx`.
 */
export function PanelCapas({ capas, onCambiarCapas, className }: PanelCapasProps) {
  const { session } = useAuth();

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

      {CAPAS_DISPONIBLES.map((opcion) => {
        const bloqueada = !!opcion.requiereSesion && !session;
        return (
          <div key={opcion.id} className="flex items-center gap-2">
            <Checkbox
              id={`capa-${opcion.id}`}
              checked={capas[opcion.id]}
              onCheckedChange={(marcado) =>
                onCambiarCapas({ ...capas, [opcion.id]: marcado === true })
              }
            />
            <Label
              htmlFor={`capa-${opcion.id}`}
              className="flex cursor-pointer items-center gap-1 font-normal"
            >
              {opcion.etiqueta}
              {bloqueada && (
                <span
                  className="flex items-center gap-1 text-muted-foreground"
                  title="Requiere iniciar sesión"
                >
                  <Lock className="h-3 w-3" aria-hidden="true" />
                  <span className="sr-only">(requiere sesión)</span>
                </span>
              )}
            </Label>
          </div>
        );
      })}
    </div>
  );
}
