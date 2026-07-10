/**
 * Etiquetas legibles en español para las 18 variables del modelo XGBoost
 * (ver CLAUDE.md raíz, sección "Las 18 variables del modelo XGBoost" —
 * lista real en `scripts/train_model.py`, constante `FEATURES`).
 *
 * Usado por el modal UPZ para traducir `feature` (SHAP top-3/completo,
 * diagnósticos prescriptivos) a lenguaje operacional en vez de mostrar el
 * nombre de columna crudo. Si el backend agrega una variable nueva que no
 * está en este mapa, `etiquetaFeature` cae al nombre crudo — nunca rompe.
 */
const ETIQUETA_FEATURE: Record<string, string> = {
  n_delitos_upz_4sem: "Delitos último mes (UPZ)",
  n_delitos_upz_8sem: "Delitos últimos 2 meses (UPZ)",
  n_delitos_upz_12sem: "Delitos últimos 3 meses (UPZ)",
  tendencia_upz: "Tendencia mes a mes",
  n_delitos_vecinos_lag: "Delitos en UPZs vecinas",
  mes_sin: "Estacionalidad (componente seno)",
  mes_cos: "Estacionalidad (componente coseno)",
  temperatura_c: "Temperatura promedio",
  precipitacion_mm_mes: "Precipitación mensual",
  estrato_promedio_upz: "Estrato socioeconómico promedio",
  cuadrantes_por_km2: "Densidad de cuadrantes policiales",
  n_estaciones_tm: "Estaciones TransMilenio",
  dist_tm_metros: "Distancia a TransMilenio",
  ratio_nuse_criminal_upz: "Proporción de llamadas NUSE por crimen",
  km_via_intervenida_upz: "Kilómetros de vía en obra",
  n_camaras_upz: "Cámaras de seguridad",
  luminarias_led_upz: "Luminarias LED",
  tipo_crimen_cod: "Tipo de delito dominante",
};

/** Traduce un código de feature del modelo a su etiqueta en español. */
export function etiquetaFeature(feature: string): string {
  return ETIQUETA_FEATURE[feature] ?? feature;
}
