import type { RolBackend } from "@/types/api";

/**
 * Roles con acceso a Predicción (Módulo 2) y Sugerencia (Módulo 3) — matriz
 * de acceso documentada en wiki_pages/Modulos.md. CIUDADANO y visitantes sin
 * sesión NO tienen acceso a ninguno de los dos (solo lectura del mapa +
 * chatbot básico). Fuente única para no duplicar esta lista entre
 * `tab-prediccion.tsx`, `tab-sugerencia.tsx` y `modal-upz.tsx`.
 */
export const ROLES_ACCESO_OPERACIONAL: RolBackend[] = [
  "COMANDANTE_CAI",
  "ANALISTA_SDSCJ",
  "ADMIN",
];

export function tieneAccesoOperacional(rol: RolBackend | undefined): boolean {
  return !!rol && ROLES_ACCESO_OPERACIONAL.includes(rol);
}
