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
