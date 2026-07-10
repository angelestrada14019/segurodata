import { useMemo } from "react";
import { usePeriodoVigente } from "@/hooks/use-periodo-vigente";
import { usePrediccionesMes } from "@/hooks/use-predicciones-mes";
import { useUpzGeometrias } from "@/hooks/use-upz-geometrias";
import type { NivelRiesgo } from "@/lib/colores-riesgo";
import type { PrediccionRow } from "@/types/supabase";

export interface FilaTop10Riesgo {
  upzCod: string;
  upzNombre: string;
  nomLocalidad: string | null;
  prediccion: PrediccionRow;
}

/** CRÍTICO primero, BAJO último — mismo orden que pinta `leyenda-riesgo.tsx`. */
const ORDEN_RIESGO: Record<NivelRiesgo, number> = {
  CRITICO: 0,
  ALTO: 1,
  MEDIO: 2,
  BAJO: 3,
};

const TOP_N = 10;

/**
 * Top-10 UPZs en mayor riesgo del período vigente — Módulo 2 (Predicción).
 *
 * Lee `predicciones` directo vía `usePrediccionesMes` (ya escrito, Sprint 1):
 * MISMA tabla y MISMO lookup por PK (upz_cod, anio, mes) que usa POST
 * /predict (`backend/app/repositories/predictions_repo.py`) y que la RPC
 * `upz_geojson` que pinta el mapa (`supabase/migrations/20260701_0012_geojson_rpc.sql`)
 * — nunca se llama /predict en loop (112 UPZs) para construir este listado,
 * es una sola lectura de tabla ya filtrada por RLS según el rol (RLS
 * `predicciones_por_rol`, migración 0006: COMANDANTE_CAI solo ve las UPZs de
 * su cuadrante, igual que en el mapa).
 *
 * El período se resuelve con `usePeriodoVigente()` — mismo hook/mismo
 * queryKey que usa `use-diagnostico-upz.ts`, así que comparte cache si el
 * usuario ya visitó el modal o el mapa antes.
 *
 * Cada fila se enriquece con nombre/localidad desde `useUpzGeometrias()`
 * (mismo cache que ya usa el mapa y el modal UPZ — sin round-trip nuevo si
 * `/diagnostico` ya se visitó en esta sesión).
 */
export function useTop10Riesgo() {
  const periodoQuery = usePeriodoVigente();
  const periodo = periodoQuery.data;
  const listoParaConsultar = !!periodo;

  const prediccionesQuery = usePrediccionesMes(
    periodo?.anio ?? 0,
    periodo?.mes ?? 0,
    listoParaConsultar,
  );
  const upzGeometriasQuery = useUpzGeometrias();

  const filas = useMemo<FilaTop10Riesgo[]>(() => {
    if (!prediccionesQuery.data) return [];

    const geometriasPorUpz = new Map(
      upzGeometriasQuery.data?.features.map((f) => [
        f.properties.upz_cod,
        f.properties,
      ]) ?? [],
    );

    return [...prediccionesQuery.data]
      .sort((a, b) => {
        const diferencia = ORDEN_RIESGO[a.nivel_riesgo] - ORDEN_RIESGO[b.nivel_riesgo];
        // Empate de banda → orden estable por upz_cod (nunca dejar el orden
        // a la merced de lo que devuelva Postgres sin ORDER BY explícito).
        return diferencia !== 0 ? diferencia : a.upz_cod.localeCompare(b.upz_cod);
      })
      .slice(0, TOP_N)
      .map((prediccion) => {
        const propiedades = geometriasPorUpz.get(prediccion.upz_cod);
        return {
          upzCod: prediccion.upz_cod,
          upzNombre: propiedades?.upz_nombre ?? `UPZ ${prediccion.upz_cod}`,
          nomLocalidad: propiedades?.nom_localidad ?? null,
          prediccion,
        };
      });
  }, [prediccionesQuery.data, upzGeometriasQuery.data]);

  return {
    filas,
    periodo,
    isLoading:
      periodoQuery.isLoading ||
      (listoParaConsultar && prediccionesQuery.isLoading) ||
      upzGeometriasQuery.isLoading,
    error:
      periodoQuery.error ?? prediccionesQuery.error ?? upzGeometriasQuery.error ?? null,
  };
}
