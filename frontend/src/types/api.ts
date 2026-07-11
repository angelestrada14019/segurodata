/**
 * Tipos a mano del contrato del backend FastAPI — skill `backend-segurodata`.
 * NUNCA inventar campos ni renombrar: este archivo espeja el JSON exacto que
 * documenta la skill. Ante discrepancia entre este archivo y una respuesta
 * real del backend, la skill/backend mandan — reportar la discrepancia, no
 * improvisar un campo nuevo aquí.
 */

import type { NivelRiesgo } from "@/lib/colores-riesgo";

// ---------------------------------------------------------------------------
// POST /predict
// ---------------------------------------------------------------------------

export interface PredictRequest {
  upz_cod: string;
  anio: number;
  mes: number;
}

export interface PredictResponse {
  upz_cod: string;
  anio: number;
  mes: number;
  nivel_riesgo: NivelRiesgo;
  probabilidades: {
    CRITICO: number;
    ALTO: number;
    MEDIO: number;
    BAJO: number;
  };
  origen: string; // 'seed_dev' | 'notebook_04'
}

// ---------------------------------------------------------------------------
// GET /explain
// ---------------------------------------------------------------------------

export interface ShapFeatureValor {
  feature: string;
  valor: number;
}

export interface ExplainResponse {
  upz_cod: string;
  anio: number;
  mes: number;
  nivel_riesgo: NivelRiesgo;
  shap_top3: ShapFeatureValor[];
  /** Solo presente para ANALISTA_SDSCJ / ADMIN — las 18 features. */
  shap_completo?: ShapFeatureValor[];
}

// ---------------------------------------------------------------------------
// POST /graphrag
// ---------------------------------------------------------------------------

export interface GraphragRequest {
  pregunta: string;
  upz_contexto?: string;
}

export interface FuenteGraphrag {
  /** Valor real del backend: `source` de `documents_corpus` — hoy siempre
   * `RSS_ELTIEMPO`/`RSS_ESPECTADOR`/`RSS_INFORMANTE` (F10, único corpus
   * activo desde la purga de F9). `string` suelto en vez de un union
   * cerrado porque el backend no lo restringe (`app/schemas/graphrag.py`). */
  tipo: string;
  titulo: string;
  fecha: string;
  url: string | null;
}

export interface GraphragResponse {
  respuesta: string;
  fuentes: FuenteGraphrag[];
  modelo_llm: string;
  cacheado: boolean;
}

// ---------------------------------------------------------------------------
// POST /prescribe
// ---------------------------------------------------------------------------

export interface PrescribeRequest {
  upz_cod: string;
  shap_top: ShapFeatureValor[];
}

export interface DiagnosticoPrescriptivo {
  feature: string;
  diagnostico: string;
  tipo_intervencion: string;
  entidad_responsable: string;
  accion: string;
}

export interface CaiInfo {
  nombre: string;
  cuadrante_id: string;
  telefono: string | null;
}

export interface PrescribeResponse {
  upz_cod: string;
  diagnosticos: DiagnosticoPrescriptivo[];
  cai: CaiInfo;
  recomendacion_llm: string;
}

// ---------------------------------------------------------------------------
// GET /whoami
// ---------------------------------------------------------------------------

export type RolBackend =
  | "CIUDADANO"
  | "COMANDANTE_CAI"
  | "ANALISTA_SDSCJ"
  | "ADMIN";

export interface WhoamiResponse {
  rol: RolBackend;
  cuadrante_asignado: string | null;
  cuadrante_pendiente: boolean;
}

// ---------------------------------------------------------------------------
// GET /health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  version: string;
  env: string;
}

// ---------------------------------------------------------------------------
// PATCH /admin/usuarios/{user_id}/cuadrante
// ---------------------------------------------------------------------------

export interface AsignarCuadranteRequest {
  cuadrante_id: string;
}

export interface AsignarCuadranteResponse {
  user_id: string;
  cuadrante_asignado: string;
}
