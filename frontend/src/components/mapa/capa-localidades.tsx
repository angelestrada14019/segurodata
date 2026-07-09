import { GeoJsonLayer } from "@deck.gl/layers";
import type { PickingInfo } from "@deck.gl/core";
import { colorRgbaPorNivel } from "@/lib/colores-riesgo";
import type { LocalidadFeature, LocalidadFeatureCollection } from "@/types/deck";

/**
 * Factory de la capa de las 20 localidades (zoom < ZOOM_THRESHOLD) — mismo
 * patrón que `capa-upz.tsx`. La RPC `localidades_geojson` agrega la
 * geometría con `ST_Union` y el riesgo dominante con `mode()` (migración 0012).
 */
export function capaLocalidades(
  data: LocalidadFeatureCollection,
  onClick: (feature: LocalidadFeature) => void,
) {
  return new GeoJsonLayer<LocalidadFeature["properties"]>({
    id: "capa-localidades",
    data,
    pickable: true,
    stroked: true,
    filled: true,
    lineWidthMinPixels: 1.5,
    getFillColor: (f) => colorRgbaPorNivel(f.properties.nivel_riesgo),
    getLineColor: [15, 18, 24, 220],
    getLineWidth: 2,
    updateTriggers: {
      getFillColor: [data],
    },
    onClick: (info: PickingInfo<LocalidadFeature>) => {
      if (info.object) onClick(info.object);
    },
  });
}
