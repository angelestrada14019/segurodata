/**
 * Paleta de riesgo — ÚNICA fuente de verdad para todo el frontend.
 *
 * Cualquier componente que necesite pintar un `nivel_riesgo` (mapa deck.gl,
 * badges, leyenda, modal UPZ) importa de aquí. NUNCA hardcodear un color de
 * riesgo en otro archivo — si el diseño cambia, cambia una sola vez.
 *
 * CRÍTICO=morado · ALTO=rojo · MEDIO=naranja · BAJO=verde.
 * `nivel_riesgo` puede venir `null` desde las RPCs de Supabase (UPZ sin
 * predicción ese mes, o fuera del cuadrante del usuario) — SIEMPRE cae a
 * COLOR_SIN_DATOS_*, nunca a un color de riesgo por defecto que mienta sobre
 * el dato real.
 */

export type NivelRiesgo = "CRITICO" | "ALTO" | "MEDIO" | "BAJO";

export const COLOR_RIESGO_HEX = {
  CRITICO: "#7c3aed", // morado
  ALTO: "#dc2626", // rojo
  MEDIO: "#ea580c", // naranja
  BAJO: "#16a34a", // verde
} as const satisfies Record<NivelRiesgo, string>;

export const COLOR_SIN_DATOS_HEX = "#6b7280"; // gris neutro

export const COLOR_RIESGO_RGBA = {
  CRITICO: [124, 58, 237, 200],
  ALTO: [220, 38, 38, 200],
  MEDIO: [234, 88, 12, 200],
  BAJO: [22, 163, 74, 200],
} as const satisfies Record<NivelRiesgo, [number, number, number, number]>;

export const COLOR_SIN_DATOS_RGBA: [number, number, number, number] = [
  107, 114, 128, 120,
];

/** Etiqueta legible en español para UI (badges, leyenda, tooltips). */
export const ETIQUETA_RIESGO: Record<NivelRiesgo, string> = {
  CRITICO: "Crítico",
  ALTO: "Alto",
  MEDIO: "Medio",
  BAJO: "Bajo",
};

/** Type guard: valida que un string/null proveniente de Supabase sea un NivelRiesgo válido. */
export function esNivelRiesgo(valor: unknown): valor is NivelRiesgo {
  return (
    valor === "CRITICO" ||
    valor === "ALTO" ||
    valor === "MEDIO" ||
    valor === "BAJO"
  );
}

/** Devuelve el color RGBA de deck.gl para un nivel de riesgo, o gris si es null/inválido. */
export function colorRgbaPorNivel(
  nivelRiesgo: string | null | undefined,
): [number, number, number, number] {
  if (esNivelRiesgo(nivelRiesgo)) {
    return COLOR_RIESGO_RGBA[nivelRiesgo];
  }
  return COLOR_SIN_DATOS_RGBA;
}

/** Devuelve el color HEX para un nivel de riesgo, o gris si es null/inválido. */
export function colorHexPorNivel(nivelRiesgo: string | null | undefined): string {
  if (esNivelRiesgo(nivelRiesgo)) {
    return COLOR_RIESGO_HEX[nivelRiesgo];
  }
  return COLOR_SIN_DATOS_HEX;
}
