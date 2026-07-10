import { ScatterplotLayer } from "@deck.gl/layers";
import { centroideMultiPolygon } from "@/lib/geo-centroide";
import type { ChangePointRow, TipoCambio } from "@/types/supabase";
import type { LocalidadFeatureCollection } from "@/types/deck";

export interface ChangePointPunto {
  id: string;
  position: [number, number];
  localidad_cod: string;
  localidad_nom: string;
  fecha_ruptura: string;
  tipo_cambio: TipoCambio;
  magnitude: number | null;
}

/**
 * Color de marcador por tipo de cambio — aproxima los tokens
 * `--destructive`/`--success`/`--warning` del tema dark (`src/index.css`),
 * los MISMOS que usa el badge `IndicadorChangePoint`
 * (`components/prescriptivo/indicador-change-point.tsx`) para el mismo
 * concepto, así el marcador se siente coordinado con el resto de la UI.
 * deck.gl no puede leer custom properties CSS, por eso son constantes RGBA
 * numéricas — y viven aquí (no en `lib/colores-riesgo.ts`, que es la fuente
 * única de verdad SOLO para `nivel_riesgo`; `tipo_cambio` es un dominio
 * distinto, ver `types/supabase.ts`).
 */
const COLOR_TIPO_CAMBIO: Record<TipoCambio, [number, number, number, number]> = {
  ALZA: [221, 68, 68, 225],
  BAJA: [42, 189, 96, 225],
  INDEFINIDO: [246, 148, 36, 210],
};

export const ETIQUETA_TIPO_CAMBIO: Record<TipoCambio, string> = {
  ALZA: "Alza",
  BAJA: "Baja",
  INDEFINIDO: "Indefinido",
};

/**
 * Normaliza un código de localidad para hacer match entre dos fuentes que no
 * necesariamente comparten convención de formato ("01" vs "1", etc.):
 * `change_points.localidad_cod` viene de F1 DAI (columna `CMIULOCAL`) y
 * `upz_geometrias.cod_localidad` de F5 NUSE (`COD_LOCALIDAD`).
 *
 * Estado real de datos (verificado, migración
 * `supabase/migrations/20260710_0014_localidades_geojson_fallback_sin_localidad.sql`):
 * `upz_geometrias.cod_localidad` está NULL en las 112 filas — el pipeline F2
 * nunca trajo el código de localidad. Con eso, esta función de matching hoy
 * no resuelve ningún punto (0 marcadores, nunca uno mal ubicado) — queda
 * lista para cuando el backfill del mapeo UPZ→Localidad llegue (pendiente
 * como tarea de pipeline de datos aparte, fuera del alcance de este
 * dispatch), sin requerir ningún cambio en el frontend.
 */
function normalizarCodigoLocalidad(codigo: string | null | undefined): string {
  if (!codigo) return "";
  const limpio = codigo.trim();
  if (limpio === "") return "";
  const numerico = Number(limpio);
  return Number.isFinite(numerico) ? String(numerico) : limpio.toUpperCase();
}

/**
 * Resuelve la posición de cada `change_point` al centroide de su localidad,
 * reusando la MISMA colección que ya consume `capa-localidades.tsx`
 * (`useLocalidadesGeometrias()` — sin round-trip nuevo a Supabase, ver
 * `mapa-riesgo.tsx`). `change_points` no tiene geometría propia, solo
 * `localidad_cod` (`ruptures` corre sobre F1 agregado por localidad, nunca
 * por UPZ — ver `scripts/compute_change_points.py`).
 *
 * Un change point sin localidad coincidente se descarta silenciosamente —
 * nunca se inventa una posición aproximada.
 */
export function resolverCentroidesChangePoints(
  changePoints: ChangePointRow[],
  localidades: LocalidadFeatureCollection,
): ChangePointPunto[] {
  const centroidesPorCodigo = new Map<string, [number, number]>();
  for (const feature of localidades.features) {
    const clave = normalizarCodigoLocalidad(feature.properties.cod_localidad);
    if (!clave || centroidesPorCodigo.has(clave)) continue;
    const centroide = centroideMultiPolygon(feature.geometry);
    if (centroide) centroidesPorCodigo.set(clave, centroide);
  }

  const puntos: ChangePointPunto[] = [];
  for (const cp of changePoints) {
    const centroide = centroidesPorCodigo.get(normalizarCodigoLocalidad(cp.localidad_cod));
    if (!centroide) continue;
    puntos.push({
      id: `${cp.localidad_cod}-${cp.fecha_ruptura}-${cp.tipo_cambio}`,
      position: centroide,
      localidad_cod: cp.localidad_cod,
      localidad_nom: cp.localidad_nom,
      fecha_ruptura: cp.fecha_ruptura,
      tipo_cambio: cp.tipo_cambio,
      magnitude: cp.magnitude,
    });
  }
  return puntos;
}

/**
 * Factory de la capa de marcadores de rupturas estructurales (`ruptures`
 * sobre F1 DAI, tabla `change_points`) — `ScatterplotLayer` en vez de
 * `IconLayer`: sin atlas de íconos que mantener, un círculo de color+tamaño
 * (por magnitud) alcanza para una capa de contexto secundaria. Recibe los
 * puntos YA resueltos (`resolverCentroidesChangePoints`) — misma separación
 * factory/datos que `capa-upz.tsx`/`capa-localidades.tsx`.
 */
export function capaChangePoints(puntos: ChangePointPunto[]) {
  return new ScatterplotLayer<ChangePointPunto>({
    id: "capa-change-points",
    data: puntos,
    pickable: true,
    stroked: true,
    filled: true,
    radiusUnits: "meters",
    radiusMinPixels: 5,
    radiusMaxPixels: 22,
    lineWidthMinPixels: 1.5,
    getPosition: (d) => d.position,
    getRadius: (d) => 220 + Math.min(Math.abs(d.magnitude ?? 0), 1) * 320,
    getFillColor: (d) => COLOR_TIPO_CAMBIO[d.tipo_cambio],
    getLineColor: [15, 18, 24, 230],
    updateTriggers: {
      getFillColor: [puntos],
      getRadius: [puntos],
    },
  });
}
