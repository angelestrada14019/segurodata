import { GeoJsonLayer } from "@deck.gl/layers";
import type { TransmilenioFeatureCollection } from "@/types/deck";

/**
 * Estaciones TransMilenio (F8) — geometría real vía RPC `transmilenio_geojson`
 * (migración `20260710_0016_infraestructura_puntual.sql`, 153 estaciones
 * extraídas de ArcGIS REST de Transmilenio S.A., `src/pipeline.py`). Antes
 * `DISPONIBLE=false`: solo existía el agregado `n_estaciones_tm`/
 * `dist_tm_metros` por UPZ (feature del modelo), sin geometría de puntos —
 * la migración 0016 agregó la tabla `transmilenio_geom` para esta capa.
 */
export const DISPONIBLE = true;

/**
 * `GeoJsonLayer` con `pointType: "circle"` — mismo enfoque que
 * `capa-cuadrantes.tsx`/`capa-upz.tsx` (RPC devuelve GeoJSON, la capa lo
 * consume directo, sin construir un array de puntos aparte). Color verde
 * agua distinto de los 4 colores de riesgo y del cian de cuadrantes/change
 * points, para no competir visualmente con la capa base.
 */
export function capaTransmilenio(data: TransmilenioFeatureCollection) {
  return new GeoJsonLayer({
    id: "capa-transmilenio",
    data,
    pickable: true,
    pointType: "circle",
    getPointRadius: 6,
    pointRadiusUnits: "pixels",
    pointRadiusMinPixels: 4,
    pointRadiusMaxPixels: 9,
    getFillColor: [16, 200, 165, 220],
    getLineColor: [15, 18, 24, 230],
    lineWidthMinPixels: 1,
    stroked: true,
    filled: true,
  });
}
