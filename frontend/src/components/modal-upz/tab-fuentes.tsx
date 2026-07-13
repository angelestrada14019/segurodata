import type { UseMutationResult } from "@tanstack/react-query";
import {
  ExternalLink,
  Loader2,
  LogIn,
  MessageSquare,
  Newspaper,
  RefreshCw,
  ScrollText,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { FuenteGraphrag, GraphragRequest, GraphragResponse } from "@/types/api";

interface TabFuentesProps {
  upzCod: string;
  /** Misma instancia de useGraphrag() que dispara tab-chatbot.tsx. */
  mutation: UseMutationResult<GraphragResponse, Error, GraphragRequest>;
  /** Cambia la pestaña activa a "chatbot" — modal-upz.tsx es dueño de ese estado. */
  onIrAChatbot: () => void;
  /** Registra el intercambio en el historial compartido — sin esto, generar
   * fuentes aquí no aparecería si el usuario después entra a Chatbot. */
  onNuevaRespuesta: (pregunta: string, respuesta: GraphragResponse) => void;
}

const PREGUNTA_AUTOGENERADA =
  "¿Qué noticias recientes de hurtos, capturas o inseguridad hay relacionadas con esta zona de Bogotá?";

const NOMBRE_MEDIO: Record<string, string> = {
  RSS_ELTIEMPO: "El Tiempo",
  RSS_ESPECTADOR: "El Espectador",
  RSS_INFORMANTE: "El Informante Soy Yo",
};

/**
 * Pestaña Fuentes — antes puramente derivada del estado de la pestaña
 * Chatbot (solo mostraba algo si el usuario ya había preguntado allá). Ahora
 * también puede disparar su propia consulta con una pregunta genérica fija,
 * mismo patrón "botón manual" que `tab-sugerencia.tsx` (llamada con costo de
 * LLM, nunca automática al abrir la pestaña). Sigue sin existir un endpoint
 * de "fuentes por UPZ" — por debajo esto es la misma POST /graphrag.
 */
export function TabFuentes({ upzCod, mutation, onIrAChatbot, onNuevaRespuesta }: TabFuentesProps) {
  const { session } = useAuth();

  function generar() {
    mutation.mutate(
      { pregunta: PREGUNTA_AUTOGENERADA, upz_contexto: upzCod },
      { onSuccess: (respuesta) => onNuevaRespuesta(PREGUNTA_AUTOGENERADA, respuesta) },
    );
  }

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
    // El chatbot (y por lo tanto esta pestaña) requiere sesión — cualquier
    // rol autenticado, no solo operacional (a diferencia de Predicción y
    // Sugerencia). Mismo gate que `chat-panel.tsx`.
    if (!session) {
      return (
        <Alert>
          <LogIn className="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Inicia sesión para ver fuentes</AlertTitle>
          <AlertDescription>
            El chatbot causal y sus fuentes requieren una cuenta. El mapa y el diagnóstico siguen
            disponibles sin iniciar sesión.
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <div className="flex flex-col gap-3">
        {mutation.isError && (
          <Alert variant="destructive">
            <AlertTitle>No se pudo generar</AlertTitle>
            <AlertDescription>
              {mutation.error?.message ?? "Intenta de nuevo en unos segundos."}
            </AlertDescription>
          </Alert>
        )}
        <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border p-8 text-center">
          <ScrollText className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
          <p className="max-w-sm text-sm text-muted-foreground">
            Genera fuentes citadas para esta UPZ, o hazle una pregunta específica en la pestaña
            Chatbot.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            <Button type="button" onClick={generar}>
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              Generar fuentes de esta UPZ
            </Button>
            <Button type="button" variant="outline" onClick={onIrAChatbot}>
              <MessageSquare className="h-3.5 w-3.5" aria-hidden="true" />
              Ir al Chatbot
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const { fuentes, modelo_llm, cacheado } = mutation.data;

  if (fuentes.length === 0) {
    return (
      <div className="flex flex-col gap-3">
        <div
          role="status"
          className="rounded-md border border-border bg-card p-6 text-center text-sm text-muted-foreground"
        >
          La última respuesta no citó fuentes específicas para esta zona.
        </div>
        <Button type="button" variant="outline" size="sm" onClick={generar} className="w-fit">
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Intentar de nuevo
        </Button>
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
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Generado con <span className="font-mono-data">{modelo_llm}</span>
          {cacheado ? " · respuesta servida desde caché" : ""}
        </p>
        <Button type="button" variant="outline" size="sm" onClick={generar}>
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Regenerar
        </Button>
      </div>
    </div>
  );
}

function FilaFuente({ fuente }: { fuente: FuenteGraphrag }) {
  const nombreMedio = NOMBRE_MEDIO[fuente.tipo] ?? "Noticia";

  return (
    <li className="flex items-start gap-3 rounded-md border border-border bg-card p-3">
      <Newspaper className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] font-mono-data uppercase">
            {nombreMedio}
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
