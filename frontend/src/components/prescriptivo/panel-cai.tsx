import { Building2, Phone } from "lucide-react";
import type { CaiInfo } from "@/types/api";

interface PanelCaiProps {
  cai: CaiInfo;
}

/**
 * Bloque "CAI responsable" — nombre, cuadrante y teléfono del CAI de Policía
 * que debe intervenir sobre la UPZ diagnosticada. Extraído de
 * `tab-sugerencia.tsx` (modal UPZ) para compartirlo con
 * `routes/modulo3-prescriptivo.tsx` (vista standalone) — ambos consumen la
 * misma forma exacta de `PrescribeResponse.cai` (POST /prescribe, skill
 * backend-segurodata). Nunca reintroducir este JSX inline en otro lugar.
 */
export function PanelCai({ cai }: PanelCaiProps) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
        CAI responsable
      </div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
        <span className="font-medium text-foreground">{cai.nombre}</span>
        <span className="font-mono-data text-xs text-muted-foreground">
          Cuadrante {cai.cuadrante_id}
        </span>
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <Phone className="h-3.5 w-3.5" aria-hidden="true" />
          {cai.telefono ?? "No registrado"}
        </span>
      </div>
    </div>
  );
}
