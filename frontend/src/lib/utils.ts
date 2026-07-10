import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const MESES_ES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
] as const;

/**
 * Formatea un período (anio, mes) como "julio 2026" — usado en el modal UPZ
 * y en cualquier lugar que muestre el período de una predicción.
 */
export function formatearPeriodo(anio: number, mes: number): string {
  const nombreMes = MESES_ES[mes - 1] ?? `mes ${mes}`;
  return `${nombreMes} ${anio}`;
}
