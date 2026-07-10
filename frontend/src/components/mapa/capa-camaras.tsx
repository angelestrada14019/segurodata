/**
 * Cámaras Salvavidas SDM (F13) — sin geometría real disponible todavía.
 * `n_camaras_upz` entra al modelo XGBoost como placeholder=0 hasta que exista
 * el extractor (ver `CLAUDE.md` raíz, tabla de las 18 variables). `DISPONIBLE`
 * lo consume `panel-capas.tsx` para deshabilitar el checkbox de esta capa —
 * nunca se inventa una geometría de cámaras para "completar" el mapa.
 */
export const DISPONIBLE = false;
