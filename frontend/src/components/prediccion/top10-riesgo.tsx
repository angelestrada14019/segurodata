import { useState, type KeyboardEvent } from "react";
import { ListOrdered } from "lucide-react";
import { useTop10Riesgo, type FilaTop10Riesgo } from "@/hooks/use-top10-riesgo";
import { ModalUpz } from "@/components/modal-upz/modal-upz";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { FilaTablaSkeleton } from "@/components/shared/loading-states";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn, formatearPeriodo } from "@/lib/utils";
import { ETIQUETA_RIESGO, type NivelRiesgo } from "@/lib/colores-riesgo";
import type { PrediccionRow } from "@/types/supabase";

const COLUMNAS = 4;
const FILAS_SKELETON = 10;

/** Probabilidad de la banda predicha — misma fila de `predicciones` que ya
 * consume el mapa, ninguna llamada nueva. */
const PROB_POR_NIVEL: Record<NivelRiesgo, (p: PrediccionRow) => number | null> = {
  CRITICO: (p) => p.prob_critico,
  ALTO: (p) => p.prob_alto,
  MEDIO: (p) => p.prob_medio,
  BAJO: (p) => p.prob_bajo,
};

/**
 * Top-10 UPZs en mayor riesgo del período vigente (Módulo 2 — Predicción) —
 * segundo punto de entrada al modal de 5 pestañas (el primero es el mapa,
 * reusado tal cual en esta misma página). Datos de `use-top10-riesgo.ts`.
 *
 * Mismo patrón de estado "sticky" que `mapa-riesgo.tsx` (léelo como
 * referencia exacta del patrón): `upzModalCod` nunca vuelve a `null` tras el
 * primer click, para que Radix Dialog pueda animar el cierre; `modalAbierto`
 * es el booleano real de open/close. Instancia INDEPENDIENTE del modal que
 * abre el mapa de esta misma página — ambas usan el mismo componente
 * `<ModalUpz>` y el mismo patrón de estado, pero no comparten una única
 * instancia montada (no hay necesidad: nunca hay más de un click a la vez).
 *
 * Abre siempre en la pestaña "prediccion" — a diferencia del mapa de
 * `/diagnostico` (pestaña "descripcion" por defecto), es la razón de ser de
 * esta entrada al modal.
 */
export function Top10Riesgo() {
  const { filas, periodo, isLoading, error } = useTop10Riesgo();

  const [upzModalCod, setUpzModalCod] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);

  function abrirUpz(upzCod: string) {
    setUpzModalCod(upzCod);
    setModalAbierto(true);
  }

  return (
    <div className="flex flex-col gap-3">
      <header className="flex items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-1.5 font-mono-data text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          <ListOrdered className="h-3.5 w-3.5" aria-hidden="true" />
          Top 10 · Mayor riesgo
        </h2>
        {periodo && (
          <span className="font-mono-data text-xs text-muted-foreground">
            {formatearPeriodo(periodo.anio, periodo.mes)}
          </span>
        )}
      </header>

      <div className="overflow-hidden rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-10">#</TableHead>
              <TableHead>UPZ</TableHead>
              <TableHead>Riesgo</TableHead>
              <TableHead className="text-right">Prob.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading &&
              filas.length === 0 &&
              Array.from({ length: FILAS_SKELETON }).map((_, i) => (
                <FilaTablaSkeleton key={i} columnas={COLUMNAS} />
              ))}

            {!isLoading && error && (
              <TableRow>
                <TableCell
                  colSpan={COLUMNAS}
                  className="p-6 text-center text-sm text-destructive"
                >
                  No se pudo cargar el top 10 de riesgo.
                </TableCell>
              </TableRow>
            )}

            {!isLoading && !error && filas.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={COLUMNAS}
                  className="p-6 text-center text-sm text-muted-foreground"
                >
                  Sin predicciones disponibles para el período vigente.
                </TableCell>
              </TableRow>
            )}

            {filas.map((fila, indice) => (
              <FilaTop10
                key={fila.upzCod}
                posicion={indice + 1}
                fila={fila}
                seleccionada={fila.upzCod === upzModalCod}
                onAbrir={() => abrirUpz(fila.upzCod)}
              />
            ))}
          </TableBody>
        </Table>
      </div>

      {upzModalCod && (
        <ModalUpz
          upzCod={upzModalCod}
          open={modalAbierto}
          onOpenChange={setModalAbierto}
          tabInicial="prediccion"
        />
      )}
    </div>
  );
}

interface FilaTop10Props {
  posicion: number;
  fila: FilaTop10Riesgo;
  seleccionada: boolean;
  onAbrir: () => void;
}

/** Fila clickeable de la tabla — target grande (toda la fila, no solo un
 * botón), operable con mouse y teclado (Enter/Espacio, `tabIndex`,
 * `aria-label` describiendo la acción completa). */
function FilaTop10({ posicion, fila, seleccionada, onAbrir }: FilaTop10Props) {
  const { prediccion, upzNombre, nomLocalidad } = fila;
  const probabilidad = PROB_POR_NIVEL[prediccion.nivel_riesgo](prediccion);

  function onKeyDown(evento: KeyboardEvent<HTMLTableRowElement>) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      onAbrir();
    }
  }

  return (
    <TableRow
      role="button"
      tabIndex={0}
      onClick={onAbrir}
      onKeyDown={onKeyDown}
      aria-label={`Ver predicción de ${upzNombre}, riesgo ${ETIQUETA_RIESGO[prediccion.nivel_riesgo].toLowerCase()}`}
      className={cn(
        "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset",
        seleccionada && "bg-muted",
      )}
    >
      <TableCell className="font-mono-data text-xs text-muted-foreground">
        {posicion}
      </TableCell>
      <TableCell>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-foreground">{upzNombre}</span>
          <span className="font-mono-data text-xs text-muted-foreground">
            {fila.upzCod}
            {nomLocalidad ? ` · ${nomLocalidad}` : ""}
          </span>
        </div>
      </TableCell>
      <TableCell>
        <BadgeNivelRiesgo nivelRiesgo={prediccion.nivel_riesgo} />
      </TableCell>
      <TableCell className="text-right font-mono-data text-xs text-muted-foreground">
        {probabilidad !== null ? `${Math.round(probabilidad * 100)}%` : "—"}
      </TableCell>
    </TableRow>
  );
}
