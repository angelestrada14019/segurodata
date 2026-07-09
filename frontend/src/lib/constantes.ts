/**
 * Constantes globales del frontend — zoom, viewport inicial del mapa, roles.
 */

/** Umbral de zoom deck.gl: <12 muestra Localidades, >=12 muestra las 112 UPZs. */
export const ZOOM_THRESHOLD = 12;

/** Viewport inicial centrado en Bogotá (react-map-gl / deck.gl InitialViewState). */
export const VIEWPORT_INICIAL_BOGOTA = {
  longitude: -74.1,
  latitude: 4.65,
  zoom: 11,
  pitch: 0,
  bearing: 0,
} as const;

/** Estilo base MapLibre sin token — demo tiles de CARTO (dark, coherente con el tema). */
export const MAPLIBRE_STYLE_URL =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export const ROLES = [
  "CIUDADANO",
  "COMANDANTE_CAI",
  "ANALISTA_SDSCJ",
  "ADMIN",
] as const;

export type Rol = (typeof ROLES)[number];
