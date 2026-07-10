/**
 * Estaciones TransMilenio (F8) — sin tabla de puntos en Supabase. Solo existe
 * el conteo agregado `n_estaciones_tm`/`dist_tm_metros` por UPZ en
 * `silver_upz_mes` (feature del modelo XGBoost), no hay geometría de
 * estaciones individuales para dibujar. `DISPONIBLE` lo consume
 * `panel-capas.tsx` para deshabilitar el checkbox de esta capa — nunca se
 * inventa una geometría de estaciones para "completar" el mapa.
 */
export const DISPONIBLE = false;
