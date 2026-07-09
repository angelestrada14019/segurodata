import { useCallback, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import type { MapViewState } from "@deck.gl/core";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { useLocalidadesGeometrias } from "@/hooks/use-localidades-geometrias";
import { useZoomAdaptativo } from "@/hooks/use-zoom-adaptativo";
import { capaUpz } from "@/components/mapa/capa-upz";
import { capaLocalidades } from "@/components/mapa/capa-localidades";
import { LeyendaRiesgo } from "@/components/mapa/leyenda-riesgo";
import { MapaSkeleton } from "@/components/shared/loading-states";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { MAPLIBRE_STYLE_URL, VIEWPORT_INICIAL_BOGOTA } from "@/lib/constantes";
import type { LocalidadFeature, UpzFeature } from "@/types/deck";

type FeatureSeleccionado =
  | { tipo: "upz"; feature: UpzFeature }
  | { tipo: "localidad"; feature: LocalidadFeature }
  | null;

/**
 * Mapa principal del Módulo 1 — Diagnóstico. DeckGL + MapLibre (react-map-gl)
 * sin token, centrado en Bogotá. Zoom adaptativo: <12 agrega por localidad,
 * >=12 muestra las 112 UPZs individuales (ver `use-zoom-adaptativo.ts`).
 *
 * `onClick` de las capas es no-op en este Sprint — el modal de 5 pestañas
 * por UPZ se cablea en Sprint 2. Aquí solo se guarda el feature en estado
 * local para mostrar un panel de detalle mínimo (nombre + badge de riesgo).
 */
export function MapaRiesgo() {
  const [viewState, setViewState] = useState<MapViewState>(
    VIEWPORT_INICIAL_BOGOTA,
  );
  const [seleccionado, setSeleccionado] = useState<FeatureSeleccionado>(null);

  const nivelAgregacion = useZoomAdaptativo(viewState.zoom);

  const upzQuery = useUpzGeometrias();
  const localidadesQuery = useLocalidadesGeometrias();

  const cargando =
    nivelAgregacion === "upz" ? upzQuery.isLoading : localidadesQuery.isLoading;
  const error =
    nivelAgregacion === "upz" ? upzQuery.error : localidadesQuery.error;

  const onClickUpz = useCallback((feature: UpzFeature) => {
    setSeleccionado({ tipo: "upz", feature });
  }, []);

  const onClickLocalidad = useCallback((feature: LocalidadFeature) => {
    setSeleccionado({ tipo: "localidad", feature });
  }, []);

  const layers = useMemo(() => {
    if (nivelAgregacion === "upz") {
      if (!upzQuery.data) return [];
      return [capaUpz(upzQuery.data, onClickUpz)];
    }
    if (!localidadesQuery.data) return [];
    return [capaLocalidades(localidadesQuery.data, onClickLocalidad)];
  }, [nivelAgregacion, upzQuery.data, localidadesQuery.data, onClickUpz, onClickLocalidad]);

  if (cargando && layers.length === 0) {
    return <MapaSkeleton />;
  }

  if (error) {
    return (
      <div
        role="alert"
        className="flex h-full w-full flex-col items-center justify-center gap-2 bg-card p-8 text-center"
      >
        <p className="font-medium text-destructive">
          No se pudo cargar el mapa de riesgo
        </p>
        <p className="max-w-md text-sm text-muted-foreground">
          {error instanceof Error ? error.message : "Error desconocido"}
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: siguiente }) =>
          setViewState(siguiente as MapViewState)
        }
        controller
        layers={layers}
        getTooltip={({ object }) => {
          if (!object) return null;
          const nombre = object.properties?.upz_nombre ?? object.properties?.nom_localidad;
          const nivel = object.properties?.nivel_riesgo ?? "SIN_DATOS";
          return {
            html: `<div style="font-family: var(--font-mono, monospace); font-size: 12px;"><strong>${nombre}</strong><br/>Riesgo: ${nivel}</div>`,
            style: {
              backgroundColor: "#0f1218",
              color: "#e5e7eb",
              border: "1px solid #2a2f3a",
              borderRadius: "2px",
              padding: "6px 8px",
            },
          };
        }}
      >
        <MapLibreMap mapStyle={MAPLIBRE_STYLE_URL} reuseMaps />
      </DeckGL>

      <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-4">
        <div className="pointer-events-auto flex items-start justify-between gap-4">
          <div className="rounded-md border border-border bg-card/95 px-3 py-2 font-mono-data text-xs text-muted-foreground shadow-lg backdrop-blur-sm">
            <span className="uppercase tracking-wide">
              {nivelAgregacion === "upz" ? "112 UPZ" : "20 localidades"}
            </span>
            <span className="mx-1.5 text-border">·</span>
            <span>zoom {viewState.zoom.toFixed(1)}</span>
          </div>

          {seleccionado && (
            <div className="pointer-events-auto flex items-center gap-2 rounded-md border border-border bg-card/95 px-3 py-2 shadow-lg backdrop-blur-sm">
              <span className="font-medium">
                {seleccionado.tipo === "upz"
                  ? seleccionado.feature.properties.upz_nombre
                  : seleccionado.feature.properties.nom_localidad}
              </span>
              <BadgeNivelRiesgo
                nivelRiesgo={seleccionado.feature.properties.nivel_riesgo}
              />
            </div>
          )}
        </div>

        <div className="pointer-events-auto self-start">
          <LeyendaRiesgo />
        </div>
      </div>
    </div>
  );
}
