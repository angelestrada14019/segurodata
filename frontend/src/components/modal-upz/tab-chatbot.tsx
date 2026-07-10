import type { UseMutationResult } from "@tanstack/react-query";
import { ChatPanel } from "@/components/chatbot/chat-panel";
import type { MensajeChat } from "@/components/modal-upz/tipos";
import type { GraphragRequest, GraphragResponse } from "@/types/api";

interface TabChatbotProps {
  upzCod: string;
  /** Misma instancia de useGraphrag() que lee tab-fuentes.tsx — vive en modal-upz.tsx. */
  mutation: UseMutationResult<GraphragResponse, Error, GraphragRequest>;
  /** Transcripción acumulada — vive en modal-upz.tsx porque Radix Tabs
   * desmonta el contenido de esta pestaña al cambiar de tab; si viviera
   * aquí como estado local se perdería cada vez que el usuario mira otra
   * pestaña y vuelve. */
  historial: MensajeChat[];
  onNuevaRespuesta: (pregunta: string, respuesta: GraphragResponse) => void;
}

/**
 * Pestaña Chatbot del modal UPZ — wrapper delgado sobre `ChatPanel`
 * (`components/chatbot/chat-panel.tsx`), extraído en Módulo 4 para
 * reusarse también en `/chatbot` standalone
 * (`routes/modulo4-chatbot.tsx`). Mismo comportamiento exacto de antes de
 * la extracción: `upzCod` siempre presente aquí (a diferencia de
 * `/chatbot`, que monta `ChatPanel` sin UPZ — consulta general).
 */
export function TabChatbot({
  upzCod,
  mutation,
  historial,
  onNuevaRespuesta,
}: TabChatbotProps) {
  return (
    <ChatPanel
      upzCod={upzCod}
      mutation={mutation}
      historial={historial}
      onNuevaRespuesta={onNuevaRespuesta}
    />
  );
}
