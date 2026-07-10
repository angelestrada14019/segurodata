import { GeoJsonLayer } from "@deck.gl/layers";
import type { CuadranteFeatureCollection } from "@/types/deck";

/**
 * Factory de la capa opcional de cuadrantes de policía — mismo patrón que
 * `capa-upz.tsx`/`capa-localidades.tsx` (`GeoJsonLayer` sobre la RPC
 * `cuadrantes_geojson`, migración 0012, servida por `use-cuadrantes-geometrias.ts`).
 *
 * Borde visible con relleno casi transparente (alpha ~7%) a propósito: esta
 * capa es contexto operativo (límites de cuadrante + CAI responsable), NO un
 * segundo mapa de riesgo — no debe competir visualmente con el color de
 * riesgo de la capa UPZ/localidad que queda debajo. Color cian, coherente con
 * el token `--accent`/`--info` del tema (`index.css`), distinto de los 4
 * colores de riesgo (`lib/colores-riesgo.ts`) y de los colores de
 * `capa-change-points.tsx`.
 */
export function capaCuadrantes(data: CuadranteFeatureCollection) {
  return new GeoJsonLayer({
    id: "capa-cuadrantes",
    data,
    pickable: true,
    stroked: true,
    filled: true,
    lineWidthMinPixels: 1.25,
    getFillColor: [31, 184, 214, 18],
    getLineColor: [31, 184, 214, 210],
    getLineWidth: 1,
  });
}
