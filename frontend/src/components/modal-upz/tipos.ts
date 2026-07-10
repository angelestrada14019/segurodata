import type { FuenteGraphrag } from "@/types/api";

/**
 * Tipos compartidos entre los tabs del modal UPZ. `MensajeChat` es un tipo
 * de UI (no forma parte del contrato del backend) — el backend es
 * stateless por diseño (`POST /graphrag` no tiene noción de conversación),
 * el historial de turnos lo arma el frontend acumulando respuestas.
 */
export interface MensajeChat {
  id: string;
  rol: "usuario" | "asistente";
  texto: string;
  fuentes?: FuenteGraphrag[];
}

/**
 * Las 5 pestañas del modal UPZ — única fuente de verdad del orden/etiquetas
 * (consumida por `modal-upz.tsx`). `TabModalUpz` la usan también los
 * segundos puntos de entrada al modal (`mapa-riesgo.tsx` reusado en Módulo 2,
 * `top10-riesgo.tsx`) para pedir una pestaña inicial distinta de
 * "descripcion" — ver prop `tabInicial` de `<ModalUpz>`.
 */
export const PESTANAS_MODAL_UPZ = [
  { valor: "descripcion", etiqueta: "Descripción" },
  { valor: "prediccion", etiqueta: "Predicción" },
  { valor: "sugerencia", etiqueta: "Sugerencia" },
  { valor: "fuentes", etiqueta: "Fuentes" },
  { valor: "chatbot", etiqueta: "Chatbot" },
] as const;

export type TabModalUpz = (typeof PESTANAS_MODAL_UPZ)[number]["valor"];
