/**
 * Tipos a mano de las tablas de Supabase relevantes para el frontend —
 * skill `supabase-segurodata`. Solo se tipan las columnas consumidas
 * directamente por supabase-js (predicciones, shap_values, silver_upz_mes,
 * change_points, upz_geometrias, cuadrantes_geom). Ante discrepancia con
 * una migración real, la migración manda.
 */

import type { NivelRiesgo } from "@/lib/colores-riesgo";

export interface PrediccionRow {
  upz_cod: string;
  anio: number;
  mes: number;
  nivel_riesgo: NivelRiesgo;
  prob_critico: number | null;
  prob_alto: number | null;
  prob_medio: number | null;
  prob_bajo: number | null;
  origen: string;
}

export interface ShapValueRow {
  upz_cod: string;
  anio: number;
  mes: number;
  feature: string;
  valor: number;
  origen: string;
}

export interface UpzGeometriaRow {
  upz_cod: string;
  upz_nombre: string | null;
  cod_localidad: string | null;
  nom_localidad: string | null;
  // geom se consume vía las RPC *_geojson, no se lee la columna PostGIS cruda.
}

export interface CuadranteGeomRow {
  cuadrante_id: string;
  nom_cai: string | null;
  upz_codes: string[] | null;
}

export type TipoCambio = "ALZA" | "BAJA" | "INDEFINIDO";

export interface ChangePointRow {
  localidad_cod: string;
  localidad_nom: string;
  fecha_ruptura: string; // date ISO
  tipo_cambio: TipoCambio;
  magnitude: number;
}

/** Subconjunto de `silver_upz_mes` usado por el mapa/Realtime del Módulo 1. */
export interface SilverUpzMesRow {
  upz_cod: string;
  anio: number;
  mes: number;
  tipo_crimen: string | null;
  es_crimen: boolean;
}

export type RolUsuario =
  | "CIUDADANO"
  | "COMANDANTE_CAI"
  | "ANALISTA_SDSCJ"
  | "ADMIN";

export interface UserProfileRow {
  user_id: string;
  email: string;
  rol: RolUsuario;
  cuadrante_asignado: string | null;
  aprobado: boolean;
}
