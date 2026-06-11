-- SeguroData — Migración 0011: columna metadata JSONB para traceability FTI
-- Agrega auditabilidad al pipeline de inferencia: guarda el vector de features
-- y metadatos del run (model_version, pipeline_run_date) junto a cada predicción.
-- Columna nullable — no rompe predicciones existentes (seed_dev ni notebook_04).

ALTER TABLE predicciones
  ADD COLUMN IF NOT EXISTS metadata JSONB;

ALTER TABLE shap_values
  ADD COLUMN IF NOT EXISTS metadata JSONB;

COMMENT ON COLUMN predicciones.metadata IS
  'Trazabilidad FTI: {"model_version": "xgboost_v1", "pipeline_run": "2026-06-xx", "features": {...}}';

COMMENT ON COLUMN shap_values.metadata IS
  'Trazabilidad FTI: {"model_version": "xgboost_v1", "pipeline_run": "2026-06-xx"}';
