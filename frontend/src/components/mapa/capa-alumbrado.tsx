import { GeoJsonLayer } from "@deck.gl/layers";
import type { AlumbradoFeature, AlumbradoFeatureCollection } from "@/types/deck";

/**
 * Alumbrado público UAESP (F14) — geometría real vía RPC `alumbrado_geojson`
 * (migración `20260710_0016_infraestructura_puntual.sql`, reusa
 * `upz_geometrias`, agrega `luminarias_led_upz` por UPZ desde ArcGIS REST
 * de Catastro Bogotá, `src/pipeline.py`). Antes `DISPONIBLE=false`: no
 * existía extractor ni geometría — ambos se implementaron el 10-jul
 * (`luminarias_led_upz` resultó ser la 3ra feature más importante del
 * modelo, ver `datos/modelos/metricas.json`).
 */
export const DISPONIBLE = true;

/**
 * Máximo observado (dic-2025 a jul-2026) ~7,400 luminarias/UPZ — se usa como
 * techo del degradado para que una sola UPZ atípica no aplaste el contraste
 * del resto. Escala raíz cuadrada (no lineal): la distribución real está
 * muy sesgada hacia valores bajos, sqrt reparte mejor el contraste visual.
 */
const MAX_LUMINARIAS_ESCALA = 7500;

function intensidad(luminarias: number): number {
  return Math.min(1, Math.sqrt(luminarias / MAX_LUMINARIAS_ESCALA));
}

/**
 * Choropleth por UPZ coloreado según `luminarias_led_upz` — mismo enfoque
 * que `capa-cuadrantes.tsx` (RPC devuelve GeoJSON MultiPolygon, la capa lo
 * consume directo). Ámbar (asociación intuitiva con iluminación), degradado
 * de intensidad en vez de paleta discreta — es una magnitud continua, no
 * una categoría como `nivel_riesgo`. Independiente de la paleta de riesgo
 * (`lib/colores-riesgo.ts`) a propósito: esta capa no es un segundo mapa de
 * riesgo, es contexto de infraestructura.
 */
export function capaAlumbrado(data: AlumbradoFeatureCollection) {
  return new GeoJsonLayer<AlumbradoFeature["properties"]>({
    id: "capa-alumbrado",
    data,
    pickable: true,
    stroked: true,
    filled: true,
    lineWidthMinPixels: 1,
    getFillColor: (f) => {
      const t = intensidad(f.properties.luminarias_led_upz ?? 0);
      return [255, 191, 36, Math.round(18 + t * 150)];
    },
    getLineColor: [255, 191, 36, 160],
    getLineWidth: 1,
    updateTriggers: {
      getFillColor: [data],
    },
  });
}
