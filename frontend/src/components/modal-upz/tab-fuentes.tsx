import type { UseMutationResult } from "@tanstack/react-query";
import { ExternalLink, Loader2, MessageSquare, Newspaper, ScrollText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { FuenteGraphrag, GraphragRequest, GraphragResponse } from "@/types/api";

interface TabFuentesProps {
  /** Misma instancia de useGraphrag() que dispara tab-chatbot.tsx — solo lectura aquí. */
  mutation: UseMutationResult<GraphragResponse, Error, GraphragRequest>;
  /** Cambia la pestaña activa a "chatbot" — modal-upz.tsx es dueño de ese estado. */
  onIrAChatbot: () => void;
}

/**
 * Pestaña Fuentes — NO existe un endpoint de fuentes por UPZ. Las únicas
 * `fuentes` disponibles vienen adjuntas a la última respuesta de
 * POST /graphrag, así que esta pestaña es puramente derivada del estado de
 * la mutación compartida (nunca dispara su propia llamada).
 */
export function TabFuentes({ mutation, onIrAChatbot }: TabFuentesProps) {
  if (mutation.isPending) {
    return (
      <div
        role="status"
        className="flex flex-col items-center gap-3 rounded-md border border-border bg-card p-8 text-center"
      >
        <Loader2 className="h-6 w-6 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">Buscando fuentes citadas…</p>
      </div>
    );
  }

  if (!mutation.data) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
        <ScrollText className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
        <p className="max-w-sm text-sm text-muted-foreground">
          Hazle una pregunta en la pestaña Chatbot para ver sus fuentes.
        </p>
        <Button type="button" variant="outline" size="sm" onClick={onIrAChatbot}>
          <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
          Ir al Chatbot
        </Button>
      </div>
    );
  }

  const { fuentes, modelo_llm, cacheado } = mutation.data;

  if (fuentes.length === 0) {
    return (
      <div
        role="status"
        className="rounded-md border border-border bg-card p-6 text-center text-sm text-muted-foreground"
      >
        La última respuesta del chatbot no citó fuentes específicas.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <ul className="flex flex-col gap-2">
        {fuentes.map((fuente, indice) => (
          <FilaFuente key={`${fuente.tipo}-${fuente.titulo}-${indice}`} fuente={fuente} />
        ))}
      </ul>
      <p className="text-xs text-muted-foreground">
        Generado con <span className="font-mono-data">{modelo_llm}</span>
        {cacheado ? " · respuesta servida desde caché" : ""}
      </p>
    </div>
  );
}

function FilaFuente({ fuente }: { fuente: FuenteGraphrag }) {
  const Icono = fuente.tipo === "BOLETIN" ? ScrollText : Newspaper;

  return (
    <li className="flex items-start gap-3 rounded-md border border-border bg-card p-3">
      <Icono className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] font-mono-data uppercase">
            {fuente.tipo === "BOLETIN" ? "Boletín SCJ" : "Noticia"}
          </Badge>
          <span className="font-mono-data text-xs text-muted-foreground">
            {formatearFecha(fuente.fecha)}
          </span>
        </div>
        <p className="mt-1 text-sm text-foreground">{fuente.titulo}</p>
        {fuente.url ? (
          <a
            href={fuente.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-flex items-center gap-1 text-xs text-primary hover:underline"
          >
            Ver fuente original
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
        ) : (
          <span className="mt-1 inline-block text-xs text-muted-foreground">
            Sin enlace directo
          </span>
        )}
      </div>
    </li>
  );
}

function formatearFecha(fecha: string): string {
  const parsed = new Date(fecha);
  if (Number.isNaN(parsed.getTime())) return fecha;
  return new Intl.DateTimeFormat("es-CO", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(parsed);
}
