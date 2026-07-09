import { GeoJsonLayer } from "@deck.gl/layers";
import type { PickingInfo } from "@deck.gl/core";
import { colorRgbaPorNivel } from "@/lib/colores-riesgo";
import type { UpzFeature, UpzFeatureCollection } from "@/types/deck";

/**
 * Factory de la capa de las 112 UPZs — patrón estándar deck.gl (función que
 * devuelve una instancia de Layer, no un componente React).
 *
 * Usa `GeoJsonLayer` (NO `PolygonLayer`): la RPC `upz_geojson` devuelve
 * geometría `MultiPolygon` ya construida en Postgres vía `ST_AsGeoJSON`
 * (migración 0012), y `PolygonLayer` espera arrays planos de coordenadas,
 * no GeoJSON.
 */
export function capaUpz(
  data: UpzFeatureCollection,
  onClick: (feature: UpzFeature) => void,
) {
  return new GeoJsonLayer<UpzFeature["properties"]>({
    id: "capa-upz",
    data,
    pickable: true,
    stroked: true,
    filled: true,
    lineWidthMinPixels: 1,
    getFillColor: (f) => colorRgbaPorNivel(f.properties.nivel_riesgo),
    getLineColor: [15, 18, 24, 200],
    getLineWidth: 1,
    updateTriggers: {
      getFillColor: [data],
    },
    onClick: (info: PickingInfo<UpzFeature>) => {
      if (info.object) onClick(info.object);
    },
  });
}
