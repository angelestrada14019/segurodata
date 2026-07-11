import { GeoJsonLayer } from "@deck.gl/layers";
import type { CamaraFeatureCollection } from "@/types/deck";

/**
 * Cámaras Salvavidas SDM (F13) — geometría real vía RPC `camaras_geojson`
 * (migración `20260710_0016_infraestructura_puntual.sql`, 92 cámaras
 * extraídas de ArcGIS REST del Hub de Movilidad Bogotá, `src/pipeline.py`).
 * Antes `DISPONIBLE=false`: no existía ni extractor ni geometría — ambos se
 * implementaron el 10-jul (`n_camaras_upz` ya no es placeholder=0 en el
 * modelo, ver `scripts/train_model.py`).
 */
export const DISPONIBLE = true;

/**
 * `GeoJsonLayer` con `pointType: "circle"` — mismo enfoque que
 * `capa-transmilenio.tsx`. Color rojo-naranja distinto de TransMilenio y de
 * los 4 colores de riesgo, evoca "vigilancia/foto-detección".
 */
export function capaCamaras(data: CamaraFeatureCollection) {
  return new GeoJsonLayer({
    id: "capa-camaras",
    data,
    pickable: true,
    pointType: "circle",
    getPointRadius: 6,
    pointRadiusUnits: "pixels",
    pointRadiusMinPixels: 4,
    pointRadiusMaxPixels: 9,
    getFillColor: [235, 94, 40, 220],
    getLineColor: [15, 18, 24, 230],
    lineWidthMinPixels: 1,
    stroked: true,
    filled: true,
  });
}
