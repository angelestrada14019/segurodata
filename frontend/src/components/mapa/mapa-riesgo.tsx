import { useCallback, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import type { MapViewState } from "@deck.gl/core";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import { toast } from "sonner";
import "maplibre-gl/dist/maplibre-gl.css";

import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { useLocalidadesGeometrias } from "@/hooks/use-localidades-geometrias";
import { useZoomAdaptativo } from "@/hooks/use-zoom-adaptativo";
import { capaUpz } from "@/components/mapa/capa-upz";
import { capaLocalidades } from "@/components/mapa/capa-localidades";
import { LeyendaRiesgo } from "@/components/mapa/leyenda-riesgo";
import { MapaSkeleton } from "@/components/shared/loading-states";
import { BadgeNivelRiesgo } from "@/components/shared/badge-nivel-riesgo";
import { ModalUpz } from "@/components/modal-upz/modal-upz";
import type { TabModalUpz } from "@/components/modal-upz/tipos";
import { MAPLIBRE_STYLE_URL, VIEWPORT_INICIAL_BOGOTA } from "@/lib/constantes";
import type { LocalidadFeature, UpzFeature } from "@/types/deck";

type FeatureSeleccionado =
  | { tipo: "upz"; feature: UpzFeature }
  | { tipo: "localidad"; feature: LocalidadFeature }
  | null;

interface MapaRiesgoProps {
  /**
   * Pestaña con la que abre el modal UPZ al hacer click — por defecto
   * "descripcion" (Módulo 1, ver `<ModalUpz>`). Módulo 2 — Predicción reusa
   * este mismo mapa TAL CUAL (mismas capas/colores, cero duplicación) y solo
   * pasa "prediccion" aquí (`routes/modulo2-prediccion.tsx`) para que el
   * modal abra directo en la pestaña relevante para ese módulo.
   */
  tabInicialModal?: TabModalUpz;
}

/**
 * Mapa principal del Módulo 1 — Diagnóstico. DeckGL + MapLibre (react-map-gl)
 * sin token, centrado en Bogotá. Zoom adaptativo: <12 agrega por localidad,
 * >=12 muestra las 112 UPZs individuales (ver `use-zoom-adaptativo.ts`).
 *
 * Click en una UPZ (zoom>=12) guarda el feature en estado local para el
 * mini-panel (nombre + badge de riesgo, gratis en hover/selección) Y abre
 * el modal de 5 pestañas (Sprint 2, `components/modal-upz/modal-upz.tsx`).
 * Click en una LOCALIDAD (zoom<12, capa agregada) NO abre el modal — esa
 * capa agrega 5-10 UPZs bajo un único polígono sin `upz_cod` individual, no
 * hay una UPZ concreta que mostrar. Se conserva el mini-panel (sigue siendo
 * información útil) y se muestra un toast invitando a acercar el zoom, en
 * vez de abrir un modal vacío o inventar un fallback más complejo.
 *
 * También lo monta `routes/modulo2-prediccion.tsx` (Módulo 2 — Predicción)
 * sin cambio alguno de capas/colores — la única diferencia entre ambos usos
 * es `tabInicialModal`, ver arriba.
 */
export function MapaRiesgo({ tabInicialModal }: MapaRiesgoProps) {
  const [viewState, setViewState] = useState<MapViewState>(
    VIEWPORT_INICIAL_BOGOTA,
  );
  const [seleccionado, setSeleccionado] = useState<FeatureSeleccionado>(null);

  // Estado del modal UPZ separado de `seleccionado`: `upzModalCod` es
  // "sticky" (nunca vuelve a null tras el primer click en una UPZ) para que
  // <ModalUpz> permanezca montado y Radix Dialog pueda animar el cierre —
  // si el padre desmontara el modal por completo al cerrar, la transición
  // `data-[state=closed]:animate-out` nunca alcanzaría a jugar. `modalAbierto`
  // es el booleano real que controla open/close.
  const [upzModalCod, setUpzModalCod] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);

  const nivelAgregacion = useZoomAdaptativo(viewState.zoom);

  const upzQuery = useUpzGeometrias();
  const localidadesQuery = useLocalidadesGeometrias();

  const cargando =
    nivelAgregacion === "upz" ? upzQuery.isLoading : localidadesQuery.isLoading;
  const error =
    nivelAgregacion === "upz" ? upzQuery.error : localidadesQuery.error;

  const onClickUpz = useCallback((feature: UpzFeature) => {
    setSeleccionado({ tipo: "upz", feature });
    setUpzModalCod(feature.properties.upz_cod);
    setModalAbierto(true);
  }, []);

  const onClickLocalidad = useCallback((feature: LocalidadFeature) => {
    setSeleccionado({ tipo: "localidad", feature });
    toast.info("Acércate más para ver el detalle de una UPZ específica", {
      description: feature.properties.nom_localidad,
    });
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
    <div className="relative w-full">
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

      {upzModalCod && (
        <ModalUpz
          upzCod={upzModalCod}
          open={modalAbierto}
          onOpenChange={setModalAbierto}
          tabInicial={tabInicialModal}
        />
      )}
    </div>
  );
}
