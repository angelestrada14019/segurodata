/**
 * Tipos de los Feature GeoJSON que devuelven las RPCs de Supabase consumidas
 * por el mapa deck.gl (`upz_geojson`, `localidades_geojson`, `cuadrantes_geojson`
 * — migración `supabase/migrations/20260701_0012_geojson_rpc.sql`).
 *
 * La geometría es MultiPolygon (por eso el mapa usa `GeoJsonLayer` de
 * `@deck.gl/layers`, NO `PolygonLayer`).
 */

import type { Feature, FeatureCollection, MultiPolygon } from "geojson";
import type { NivelRiesgo } from "@/lib/colores-riesgo";

export interface UpzFeatureProperties {
  upz_cod: string;
  upz_nombre: string;
  cod_localidad: string;
  nom_localidad: string;
  /** null = UPZ sin predicción ese mes, o fuera del cuadrante del usuario (COMANDANTE_CAI). */
  nivel_riesgo: NivelRiesgo | null;
  prob_critico: number | null;
  prob_alto: number | null;
  prob_medio: number | null;
  prob_bajo: number | null;
}

export interface LocalidadFeatureProperties {
  cod_localidad: string;
  nom_localidad: string;
  nivel_riesgo: NivelRiesgo | null;
}

export interface CuadranteFeatureProperties {
  cuadrante_id: string;
  nom_cai: string | null;
  telefono: string | null;
}

export type UpzFeature = Feature<MultiPolygon, UpzFeatureProperties>;
export type LocalidadFeature = Feature<MultiPolygon, LocalidadFeatureProperties>;
export type CuadranteFeature = Feature<MultiPolygon, CuadranteFeatureProperties>;

export type UpzFeatureCollection = FeatureCollection<
  MultiPolygon,
  UpzFeatureProperties
>;
export type LocalidadFeatureCollection = FeatureCollection<
  MultiPolygon,
  LocalidadFeatureProperties
>;
export type CuadranteFeatureCollection = FeatureCollection<
  MultiPolygon,
  CuadranteFeatureProperties
>;

/** Nivel de agregación que decide `use-zoom-adaptativo.ts`. */
export type NivelAgregacionMapa = "localidad" | "upz";
