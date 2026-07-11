import { useCallback, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import type { LayersList, MapViewState } from "@deck.gl/core";
import { Map as MapLibreMap } from "react-map-gl/maplibre";
import { toast } from "sonner";
import "maplibre-gl/dist/maplibre-gl.css";

import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import { useLocalidadesGeometrias } from "@/hooks/use-localidades-geometrias";
import { useZoomAdaptativo } from "@/hooks/use-zoom-adaptativo";
import { useAuth } from "@/hooks/use-auth";
import { useCuadrantesGeometrias } from "@/hooks/use-cuadrantes-geometrias";
import { useTransmilenioGeometrias } from "@/hooks/use-transmilenio-geometrias";
import { useCamarasGeometrias } from "@/hooks/use-camaras-geometrias";
import { useAlumbradoGeometrias } from "@/hooks/use-alumbrado-geometrias";
import { useChangePoints } from "@/hooks/use-change-points";
import { useSilverRealtime } from "@/hooks/use-silver-realtime";
import type { Periodo } from "@/hooks/use-rango-periodos";
import { capaUpz } from "@/components/mapa/capa-upz";
import { capaLocalidades } from "@/components/mapa/capa-localidades";
import { capaCuadrantes } from "@/components/mapa/capa-cuadrantes";
import { capaTransmilenio } from "@/components/mapa/capa-transmilenio";
import { capaCamaras } from "@/components/mapa/capa-camaras";
import { capaAlumbrado } from "@/components/mapa/capa-alumbrado";
import {
  capaChangePoints,
  resolverCentroidesChangePoints,
  ETIQUETA_TIPO_CAMBIO,
  type ChangePointPunto,
} from "@/components/mapa/capa-change-points";
import { PanelCapas, type CapasVisibles } from "@/components/mapa/panel-capas";
import { SliderTemporal } from "@/components/mapa/slider-temporal";
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

const ESTILO_TOOLTIP = {
  backgroundColor: "#0f1218",
  color: "#e5e7eb",
  border: "1px solid #2a2f3a",
  borderRadius: "2px",
  padding: "6px 8px",
} as const;

const CAPAS_INICIALES: CapasVisibles = {
  cuadrantes: false,
  rupturas: false,
  transmilenio: false,
  camaras: false,
  alumbrado: false,
};

function esChangePointPunto(objeto: unknown): objeto is ChangePointPunto {
  return typeof objeto === "object" && objeto !== null && "tipo_cambio" in objeto && "position" in objeto;
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
 *
 * Capas opcionales (Sprint 2, `panel-capas.tsx`): cuadrantes de policía y
 * marcadores de rupturas estructurales (`change_points`) se suman al array
 * `layers` cuando el usuario las activa — ver `capa-cuadrantes.tsx` /
 * `capa-change-points.tsx`. El slider temporal (`slider-temporal.tsx`)
 * controla el (anio, mes) que consultan `useUpzGeometrias`/
 * `useLocalidadesGeometrias` — `periodoSeleccionado` arranca en `null` y se
 * queda así hasta que el usuario mueve el slider (comportamiento de carga
 * inicial IDÉNTICO al de antes: esos hooks resuelven "período más reciente"
 * internamente cuando `anio`/`mes` llegan `undefined`). Sembrar ese default
 * hacia este estado ni bien se resuelve el rango parecía más "completo" pero
 * dispara una segunda consulta con un query key distinto y el mapa queda un
 * instante sin capa base (parpadeo) — se descartó a propósito, ver
 * `slider-temporal.tsx`.
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
  // es el booleano real que controla open/close. El mismo "sticky" sirve
  // para la suscripción Realtime de abajo: mientras haya una UPZ
  // seleccionada en la sesión, se escuchan sus INSERTs nuevos en
  // `silver_upz_mes`, aunque el modal ya se haya cerrado.
  const [upzModalCod, setUpzModalCod] = useState<string | null>(null);
  const [modalAbierto, setModalAbierto] = useState(false);

  const [periodoSeleccionado, setPeriodoSeleccionado] = useState<Periodo | null>(null);
  const [capasVisibles, setCapasVisibles] = useState<CapasVisibles>(CAPAS_INICIALES);

  const { session } = useAuth();

  const nivelAgregacion = useZoomAdaptativo(viewState.zoom);

  const upzQuery = useUpzGeometrias(periodoSeleccionado?.anio, periodoSeleccionado?.mes);
  const localidadesQuery = useLocalidadesGeometrias(
    periodoSeleccionado?.anio,
    periodoSeleccionado?.mes,
  );
  // `cuadrantes_geojson` es RPC `authenticated`-only (migración 0012, expone
  // nombre de CAI + teléfono) — solo se dispara si el checkbox está activo Y
  // hay sesión, nunca para el visitante anon de /diagnostico (evita un 42501
  // de permisos innecesario).
  const cuadrantesQuery = useCuadrantesGeometrias(capasVisibles.cuadrantes && !!session);
  // transmilenio_geojson/camaras_geojson/alumbrado_geojson son lectura
  // PÚBLICA desde la migración 0018 — su data ya es abierta sin cuenta en
  // el portal de origen (ArcGIS Hub SDM/Catastro/GIS TransMilenio), así que
  // a diferencia de cuadrantes no dependen de `session`: se disparan con
  // solo el checkbox del panel de capas, igual para anon que autenticado.
  const transmilenioQuery = useTransmilenioGeometrias(capasVisibles.transmilenio);
  const camarasQuery = useCamarasGeometrias(capasVisibles.camaras);
  const alumbradoQuery = useAlumbradoGeometrias(capasVisibles.alumbrado);
  const changePointsQuery = useChangePoints();

  const cargando =
    nivelAgregacion === "upz" ? upzQuery.isLoading : localidadesQuery.isLoading;
  const error =
    nivelAgregacion === "upz" ? upzQuery.error : localidadesQuery.error;
  // `isFetching` (no `isLoading`): con `placeholderData: keepPreviousData`
  // (ver use-upz-geometrias.ts) el mapa sigue mostrando el período anterior
  // mientras el nuevo carga — a propósito, evita el parpadeo a skeleton
  // completo en cada paso del slider. Pero eso dejaba CERO señal visual
  // durante ese lapso (se veía congelado). `isFetching` sí es true en ese
  // background-refetch aunque `isLoading` sea false — es la señal que
  // `<SliderTemporal>` necesita para mostrar su propio spinner puntual.
  const actualizandoPeriodo =
    nivelAgregacion === "upz" ? upzQuery.isFetching : localidadesQuery.isFetching;

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

  const capaBase = useMemo(() => {
    if (nivelAgregacion === "upz") {
      if (!upzQuery.data) return null;
      return capaUpz(upzQuery.data, onClickUpz);
    }
    if (!localidadesQuery.data) return null;
    return capaLocalidades(localidadesQuery.data, onClickLocalidad);
  }, [nivelAgregacion, upzQuery.data, localidadesQuery.data, onClickUpz, onClickLocalidad]);

  // Centroides resueltos contra `localidadesQuery.data` — MISMA colección
  // que ya pinta `capa-localidades.tsx`, sin round-trip nuevo a Supabase
  // (backfill de `cod_localidad` corrido, ver `capa-change-points.tsx`).
  const puntosChangePoints = useMemo<ChangePointPunto[]>(() => {
    if (!changePointsQuery.data || !localidadesQuery.data) return [];
    return resolverCentroidesChangePoints(changePointsQuery.data, localidadesQuery.data);
  }, [changePointsQuery.data, localidadesQuery.data]);

  const layers = useMemo<LayersList>(
    () => [
      capaBase,
      capasVisibles.cuadrantes && cuadrantesQuery.data
        ? capaCuadrantes(cuadrantesQuery.data)
        : null,
      capasVisibles.rupturas && puntosChangePoints.length > 0
        ? capaChangePoints(puntosChangePoints)
        : null,
      capasVisibles.transmilenio && transmilenioQuery.data
        ? capaTransmilenio(transmilenioQuery.data)
        : null,
      capasVisibles.camaras && camarasQuery.data ? capaCamaras(camarasQuery.data) : null,
      capasVisibles.alumbrado && alumbradoQuery.data
        ? capaAlumbrado(alumbradoQuery.data)
        : null,
    ],
    [
      capaBase,
      capasVisibles,
      cuadrantesQuery.data,
      puntosChangePoints,
      transmilenioQuery.data,
      camarasQuery.data,
      alumbradoQuery.data,
    ],
  );

  if (cargando && !capaBase) {
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

          if (esChangePointPunto(object)) {
            const anio = object.fecha_ruptura.slice(0, 4);
            const magnitud =
              object.magnitude !== null && object.magnitude !== undefined
                ? ` (${object.magnitude > 0 ? "+" : ""}${Math.round(object.magnitude * 100)}%)`
                : "";
            return {
              html: `<div style="font-family: var(--font-mono, monospace); font-size: 12px;"><strong>${object.localidad_nom}</strong><br/>Ruptura ${anio} · ${ETIQUETA_TIPO_CAMBIO[object.tipo_cambio]}${magnitud}</div>`,
              style: ESTILO_TOOLTIP,
            };
          }

          const props = (object.properties ?? {}) as Record<string, unknown>;

          if (typeof props.cuadrante_id === "string") {
            const nomCai = typeof props.nom_cai === "string" ? props.nom_cai : null;
            return {
              html: `<div style="font-family: var(--font-mono, monospace); font-size: 12px;"><strong>${nomCai ?? "Cuadrante"}</strong><br/>Cuadrante ${props.cuadrante_id}</div>`,
              style: ESTILO_TOOLTIP,
            };
          }

          const nombre = props.upz_nombre ?? props.nom_localidad;
          const nivel = props.nivel_riesgo ?? "SIN_DATOS";
          return {
            html: `<div style="font-family: var(--font-mono, monospace); font-size: 12px;"><strong>${nombre}</strong><br/>Riesgo: ${nivel}</div>`,
            style: ESTILO_TOOLTIP,
          };
        }}
      >
        <MapLibreMap mapStyle={MAPLIBRE_STYLE_URL} reuseMaps />
      </DeckGL>

      <div className="pointer-events-none absolute inset-0 flex flex-col justify-between p-4">
        <div className="flex flex-col gap-2">
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

          <div className="pointer-events-auto flex justify-center">
            <SliderTemporal
              periodo={periodoSeleccionado}
              onCambiarPeriodo={setPeriodoSeleccionado}
              actualizando={actualizandoPeriodo}
            />
          </div>
        </div>

        <div className="pointer-events-auto flex items-end justify-between gap-4">
          <LeyendaRiesgo />
          <PanelCapas capas={capasVisibles} onCambiarCapas={setCapasVisibles} />
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

      {upzModalCod && <SilverRealtimeToast upzCod={upzModalCod} />}
    </div>
  );
}

/**
 * Suscripción Realtime a `silver_upz_mes` (`use-silver-realtime.ts`) para la
 * UPZ actualmente seleccionada — al recibir un INSERT nuevo, notifica con un
 * toast informativo (sin refetch automático, alcance mínimo a propósito).
 *
 * Componente propio en vez de un `useEffect` inline en `<MapaRiesgo>` porque
 * `useSilverRealtime` exige `upzCod: string` no-nulo y los hooks no pueden
 * llamarse condicionalmente — montar/desmontar este componente según
 * `upzModalCod` logra "solo suscribirse una vez hay UPZ seleccionada" sin
 * violar las reglas de hooks (`react/rules-of-hooks`).
 */
function SilverRealtimeToast({ upzCod }: { upzCod: string }) {
  const onInsert = useCallback(() => {
    toast.info("Nuevo dato disponible para esta UPZ", {
      description: `UPZ ${upzCod}`,
    });
  }, [upzCod]);

  useSilverRealtime(upzCod, onInsert);
  return null;
}
