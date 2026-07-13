import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import type { UseMutationResult } from "@tanstack/react-query";
import { Bot, Loader2, Lock, LogIn, Send, User } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TextoMarkdown } from "@/components/shared/texto-markdown";
import type { MensajeChat } from "@/components/modal-upz/tipos";
import type { GraphragRequest, GraphragResponse } from "@/types/api";

interface ChatPanelProps {
  /**
   * UPZ de contexto — OPCIONAL. Presente cuando `ChatPanel` se monta desde
   * la pestaña Chatbot del modal UPZ (`modal-upz/tab-chatbot.tsx`, wrapper
   * delgado con `upzCod` fijo); ausente en `/chatbot` standalone (Módulo 4,
   * `routes/modulo4-chatbot.tsx`) — consulta de contexto causal general, no
   * atada a una UPZ. Solo afecta textos de ayuda y viaja tal cual como
   * `upz_contexto` en el `mutate` (el tipo `GraphragRequest.upz_contexto?`
   * ya acepta `undefined`).
   */
  upzCod?: string;
  /** Nombre/localidad reales de la UPZ — igual que upzCod, ausentes en
   * `/chatbot` standalone. Viajan en el POST /graphrag para que el LLM sepa
   * a qué zona se refiere el código, no solo el número. */
  upzNombre?: string;
  nomLocalidad?: string;
  /** Instancia de `useGraphrag()` — compartida con la pestaña Fuentes dentro
   * del modal; propia y dedicada en `/chatbot` standalone. */
  mutation: UseMutationResult<GraphragResponse, Error, GraphragRequest>;
  /** Transcripción acumulada — vive un nivel arriba (modal-upz.tsx o
   * routes/modulo4-chatbot.tsx) porque dentro del modal Radix Tabs desmonta
   * el contenido de esta pestaña al cambiar de tab; si viviera aquí como
   * estado local se perdería cada vez que el usuario mira otra pestaña. */
  historial: MensajeChat[];
  onNuevaRespuesta: (pregunta: string, respuesta: GraphragResponse) => void;
}

/**
 * Panel de chat — POST /graphrag. Extraído de la pestaña Chatbot del modal
 * UPZ (Sprint 2) para reusarlo tal cual en `/chatbot` standalone (Módulo 4).
 * `pregunta` es estado local (no necesita sobrevivir el desmontaje: se
 * limpia en cada envío exitoso).
 */
export function ChatPanel({
  upzCod,
  upzNombre,
  nomLocalidad,
  mutation,
  historial,
  onNuevaRespuesta,
}: ChatPanelProps) {
  const { session } = useAuth();
  const [pregunta, setPregunta] = useState("");
  const finRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [historial.length, mutation.isPending]);

  if (!session) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
        <Lock className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
        <p className="max-w-sm text-sm text-muted-foreground">
          {upzCod
            ? "Inicia sesión para preguntarle al asistente sobre el contexto causal de esta UPZ."
            : "Inicia sesión para preguntarle al asistente sobre el contexto causal de la criminalidad en Bogotá."}
        </p>
        <Button asChild size="sm">
          <Link to="/login">
            <LogIn className="h-4 w-4" aria-hidden="true" />
            Ingresar
          </Link>
        </Button>
      </div>
    );
  }

  function handleSubmit(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const texto = pregunta.trim();
    if (!texto || mutation.isPending) return;

    mutation.mutate(
      { pregunta: texto, upz_contexto: upzCod, upz_nombre: upzNombre, nom_localidad: nomLocalidad },
      {
        onSuccess: (respuesta) => {
          onNuevaRespuesta(texto, respuesta);
          setPregunta("");
        },
      },
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto pr-1">
        {historial.length === 0 && !mutation.isPending ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <Bot className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
            <p className="max-w-xs text-sm text-muted-foreground">
              {upzCod
                ? `Pregunta por el contexto causal de la UPZ ${upzCod} — por ejemplo: "¿por qué subió el riesgo este mes?"`
                : 'Pregunta por el contexto causal de un hecho reciente — por ejemplo: "¿por qué subió el hurto en Kennedy este mes?"'}
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-3 pb-2">
            {historial.map((mensaje) => (
              <BurbujaMensaje key={mensaje.id} mensaje={mensaje} />
            ))}
            {mutation.isPending && (
              <li className="flex justify-start">
                <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  Consultando fuentes…
                </div>
              </li>
            )}
          </ul>
        )}
        <div ref={finRef} />
      </div>

      {mutation.isError && (
        <p role="alert" className="mb-2 text-xs text-destructive">
          {mutation.error?.message ?? "No se pudo obtener respuesta, intenta de nuevo."}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="flex shrink-0 items-center gap-2 border-t border-border pt-3"
      >
        <Input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder={upzCod ? "Escribe tu pregunta…" : "Pregunta sobre seguridad en Bogotá…"}
          disabled={mutation.isPending}
          aria-label="Pregunta para el chatbot"
        />
        <Button type="submit" size="icon" disabled={mutation.isPending || !pregunta.trim()}>
          {mutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="h-4 w-4" aria-hidden="true" />
          )}
          <span className="sr-only">Enviar pregunta</span>
        </Button>
      </form>
    </div>
  );
}

function BurbujaMensaje({ mensaje }: { mensaje: MensajeChat }) {
  const esUsuario = mensaje.rol === "usuario";

  return (
    <li className={cn("flex", esUsuario ? "justify-end" : "justify-start")}>
      <div className={cn("flex max-w-[85%] gap-2", esUsuario && "flex-row-reverse")}>
        <div
          className={cn(
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border",
            esUsuario
              ? "border-primary/40 bg-primary/10 text-primary"
              : "border-border bg-secondary text-muted-foreground",
          )}
          aria-hidden="true"
        >
          {esUsuario ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
        </div>
        <div
          className={cn(
            "rounded-md border px-3 py-2 text-sm leading-relaxed",
            esUsuario
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border bg-card text-foreground",
          )}
        >
          {esUsuario ? (
            <p className="whitespace-pre-wrap">{mensaje.texto}</p>
          ) : (
            <TextoMarkdown className="text-sm leading-relaxed">{mensaje.texto}</TextoMarkdown>
          )}
          {mensaje.fuentes && mensaje.fuentes.length > 0 && (
            // Citas inline (estilo notas al pie numeradas) en vez de remitir a
            // "la pestaña Fuentes": `ChatPanel` se monta también en
            // `/chatbot` standalone, donde no existe esa pestaña — este
            // formato funciona igual de bien en ambos contextos.
            <ol className="mt-2 flex flex-col gap-1 border-t border-border/60 pt-2">
              {mensaje.fuentes.map((fuente, indice) => (
                <li
                  key={`${fuente.tipo}-${fuente.titulo}-${indice}`}
                  className="flex items-start gap-1.5 text-xs text-muted-foreground"
                >
                  <span
                    className="mt-0.5 shrink-0 font-mono-data text-[10px] text-muted-foreground/70"
                    aria-hidden="true"
                  >
                    [{indice + 1}]
                  </span>
                  {fuente.url ? (
                    <a
                      href={fuente.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="truncate hover:text-primary hover:underline"
                    >
                      {fuente.titulo}
                    </a>
                  ) : (
                    <span className="truncate">{fuente.titulo}</span>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </li>
  );
}
