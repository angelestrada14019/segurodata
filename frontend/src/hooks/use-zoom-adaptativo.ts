import { useMemo } from "react";
import { ZOOM_THRESHOLD } from "@/lib/constantes";
import type { NivelAgregacionMapa } from "@/types/deck";

/**
 * Deriva el nivel de agregación del mapa a partir del zoom actual.
 * zoom < ZOOM_THRESHOLD (12) → 'localidad' (20 polígonos agregados).
 * zoom >= ZOOM_THRESHOLD → 'upz' (112 polígonos individuales).
 */
export function useZoomAdaptativo(zoom: number): NivelAgregacionMapa {
  return useMemo(
    () => (zoom < ZOOM_THRESHOLD ? "localidad" : "upz"),
    [zoom],
  );
}
