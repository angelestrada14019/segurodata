import type { MultiPolygon, Position } from "geojson";

/**
 * Centroide geométrico (área-ponderado) de un `MultiPolygon` GeoJSON — usado
 * para posicionar marcadores puntuales (ej. `components/mapa/capa-change-points.tsx`)
 * sobre un polígono que no trae su propio punto de referencia (`change_points`
 * está indexada por `localidad_cod`, sin geometría propia — ver
 * `scripts/compute_change_points.py`).
 *
 * Fórmula estándar del centroide de un polígono ("shoelace"/signed area):
 * https://en.wikipedia.org/wiki/Centroid#Of_a_polygon — se aplica sobre el
 * anillo EXTERIOR de cada polígono del MultiPolygon (ignora huecos/islas
 * interiores — aceptable para posicionar un marcador, no para cálculos de
 * área exactos) y se usa el polígono de MAYOR área como resultado final (el
 * "cuerpo principal" cuando el MultiPolygon trae fragmentos pequeños sueltos,
 * ej. una localidad con un enclave separado).
 *
 * Devuelve `null` si la geometría está vacía o degenerada — nunca inventa
 * una posición (ej. `[0, 0]`, medio Atlántico) para no ubicar un marcador en
 * un punto falso.
 */
export function centroideMultiPolygon(geom: MultiPolygon): [number, number] | null {
  let mejor: { areaAbs: number; cx: number; cy: number } | null = null;

  for (const poligono of geom.coordinates) {
    const resultado = centroideAnillo(poligono[0]);
    if (!resultado) continue;
    if (!mejor || resultado.areaAbs > mejor.areaAbs) {
      mejor = resultado;
    }
  }

  return mejor ? [mejor.cx, mejor.cy] : null;
}

function centroideAnillo(
  anillo: Position[] | undefined,
): { areaAbs: number; cx: number; cy: number } | null {
  if (!anillo || anillo.length < 3) return null;

  let areaAcumulada = 0;
  let cx = 0;
  let cy = 0;

  for (let i = 0; i < anillo.length - 1; i++) {
    const [x0, y0] = anillo[i];
    const [x1, y1] = anillo[i + 1];
    const cruzado = x0 * y1 - x1 * y0;
    areaAcumulada += cruzado;
    cx += (x0 + x1) * cruzado;
    cy += (y0 + y1) * cruzado;
  }

  const area = areaAcumulada / 2;
  if (area === 0) {
    // Anillo degenerado (puntos colineales) — respaldo: promedio simple de vértices.
    const n = anillo.length;
    const suma = anillo.reduce<[number, number]>(
      (acc, [x, y]) => [acc[0] + x, acc[1] + y],
      [0, 0],
    );
    return { areaAbs: 0, cx: suma[0] / n, cy: suma[1] / n };
  }

  return { areaAbs: Math.abs(area), cx: cx / (6 * area), cy: cy / (6 * area) };
}
