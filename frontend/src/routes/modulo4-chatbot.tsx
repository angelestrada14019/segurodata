import { useState } from "react";
import { ChatPanel } from "@/components/chatbot/chat-panel";
import { useGraphrag } from "@/hooks/use-graphrag";
import type { MensajeChat } from "@/components/modal-upz/tipos";
import type { GraphragResponse } from "@/types/api";

/**
 * Módulo 4 — Chatbot causal, standalone. Consulta general de contexto
 * causal (no atada a una UPZ): monta `<ChatPanel>` SIN `upzCod` — misma
 * pieza que usa la pestaña Chatbot del modal UPZ
 * (`modal-upz/tab-chatbot.tsx`), pero con su PROPIA instancia de
 * `useGraphrag()` y su PROPIO historial. A diferencia del modal, aquí no
 * hay pestaña Fuentes que comparta la mutación — POST /graphrag es
 * stateless (sin noción de conversación), el historial de turnos lo arma
 * el frontend acumulando respuestas (mismo patrón que
 * `components/modal-upz/modal-upz.tsx`, ver `handleNuevaRespuesta`); las
 * fuentes de cada respuesta se muestran inline en la burbuja
 * (`BurbujaMensaje`, dentro de `ChatPanel`).
 *
 * Roles con acceso: CIUDADANO · COMANDANTE_CAI · ANALISTA_SDSCJ · ADMIN —
 * cualquier sesión autenticada (matriz endpoint×rol, skill
 * backend-segurodata: POST /graphrag es 401 sin token, ✅ para los 4 roles
 * con token), ya filtrados por `ProtectedRoute` en App.tsx.
 */
export function ModuloChatbotPage() {
  const [historial, setHistorial] = useState<MensajeChat[]>([]);
  const graphragMutation = useGraphrag();

  function handleNuevaRespuesta(pregunta: string, respuesta: GraphragResponse) {
    setHistorial((previo) => [
      ...previo,
      { id: `general-${previo.length}-u`, rol: "usuario", texto: pregunta },
      {
        id: `general-${previo.length}-a`,
        rol: "asistente",
        texto: respuesta.respuesta,
        fuentes: respuesta.fuentes,
      },
    ]);
  }

  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <div>
        <h1 className="font-mono-data text-sm font-semibold tracking-wide uppercase">
          Módulo 4 — Chatbot causal
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Contexto causal de la criminalidad en Bogotá, con fuentes citadas
          — prensa verificada de Bogotá.
        </p>
      </div>

      <div className="flex min-h-[520px] flex-1 flex-col rounded-md border border-border bg-card p-4">
        <ChatPanel
          mutation={graphragMutation}
          historial={historial}
          onNuevaRespuesta={handleNuevaRespuesta}
        />
      </div>
    </div>
  );
}
