-- SeguroData — Migración 0006: Row Level Security
-- ⚠️ Regla D8: el backend usa SERVICE_KEY que BYPASEA RLS — estas políticas protegen
-- al FRONTEND (anon key + token de usuario). El backend duplica el filtro por rol
-- en su capa services (backend/app/services/).

ALTER TABLE silver_upz_mes   ENABLE ROW LEVEL SECURITY;
ALTER TABLE predicciones     ENABLE ROW LEVEL SECURITY;
ALTER TABLE shap_values      ENABLE ROW LEVEL SECURITY;
ALTER TABLE change_points    ENABLE ROW LEVEL SECURITY;
ALTER TABLE upz_geometrias   ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuadrantes_geom  ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents_corpus ENABLE ROW LEVEL SECURITY;

-- Lectura pública (mapa base sin login): geometrías y rupturas históricas
DROP POLICY IF EXISTS "upz_lectura_publica" ON upz_geometrias;
CREATE POLICY "upz_lectura_publica" ON upz_geometrias
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "change_points_lectura_publica" ON change_points;
CREATE POLICY "change_points_lectura_publica" ON change_points
  FOR SELECT TO anon, authenticated USING (true);

-- Cuadrantes: visibles para usuarios autenticados (capa del mapa)
DROP POLICY IF EXISTS "cuadrantes_autenticados" ON cuadrantes_geom;
CREATE POLICY "cuadrantes_autenticados" ON cuadrantes_geom
  FOR SELECT TO authenticated USING (true);

-- Silver: usuarios autenticados (Módulo 1 — diagnóstico)
DROP POLICY IF EXISTS "silver_autenticados" ON silver_upz_mes;
CREATE POLICY "silver_autenticados" ON silver_upz_mes
  FOR SELECT TO authenticated USING (true);

-- Predicciones: analista/admin todo; comandante solo UPZs de su cuadrante; ciudadano mapa completo
DROP POLICY IF EXISTS "predicciones_por_rol" ON predicciones;
CREATE POLICY "predicciones_por_rol" ON predicciones
  FOR SELECT TO authenticated
  USING (
    (auth.jwt()->>'rol') IN ('ANALISTA_SDSCJ','ADMIN','CIUDADANO')
    OR (
      (auth.jwt()->>'rol') = 'COMANDANTE_CAI'
      AND upz_cod IN (
        SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
        WHERE cg.cuadrante_id = auth.jwt()->>'cuadrante_asignado'
      )
    )
  );

-- SHAP: usuarios autenticados (el nivel de detalle top-3 vs completo lo aplica el backend)
DROP POLICY IF EXISTS "shap_autenticados" ON shap_values;
CREATE POLICY "shap_autenticados" ON shap_values
  FOR SELECT TO authenticated USING (true);

-- Corpus GraphRAG: usuarios autenticados
DROP POLICY IF EXISTS "corpus_autenticados" ON documents_corpus;
CREATE POLICY "corpus_autenticados" ON documents_corpus
  FOR SELECT TO authenticated USING (true);

-- Perfiles: cada usuario ve el suyo; ADMIN ve y edita todos
DROP POLICY IF EXISTS "perfil_propio" ON user_profiles;
CREATE POLICY "perfil_propio" ON user_profiles
  FOR SELECT TO authenticated USING (user_id = auth.uid());

DROP POLICY IF EXISTS "admin_lee_perfiles" ON user_profiles;
CREATE POLICY "admin_lee_perfiles" ON user_profiles
  FOR SELECT TO authenticated USING ((auth.jwt()->>'rol') = 'ADMIN');

DROP POLICY IF EXISTS "admin_edita_perfiles" ON user_profiles;
CREATE POLICY "admin_edita_perfiles" ON user_profiles
  FOR UPDATE TO authenticated USING ((auth.jwt()->>'rol') = 'ADMIN');

-- Lectura del hook de claims (supabase_auth_admin no pasa por las políticas anteriores)
DROP POLICY IF EXISTS "auth_admin_lee_perfiles" ON user_profiles;
CREATE POLICY "auth_admin_lee_perfiles" ON user_profiles
  FOR SELECT TO supabase_auth_admin USING (true);
