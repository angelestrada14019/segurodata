-- SeguroData — Migración 0008: fixes de los advisors de Supabase (security + performance)
-- 1. search_path fijo en funciones (lint 0011)
-- 2. handle_new_user no invocable vía PostgREST (lints 0028/0029)
-- 3. RLS con (select auth.*()) para evitar re-evaluación por fila (lint 0003)
-- 4. Fusión de políticas permisivas duplicadas en user_profiles (lint 0006)
-- 5. Índice para FK user_profiles.cuadrante_asignado (lint 0001)
-- Nota: spatial_ref_sys sin RLS y postgis/vector en schema public son limitaciones
-- de PostGIS gestionado (tabla de sistema de solo lectura, extensiones no relocalizables).

ALTER FUNCTION public.custom_access_token_hook(jsonb) SET search_path = public;
ALTER FUNCTION public.handle_new_user() SET search_path = public;
ALTER FUNCTION public.match_documents(vector, float, int, varchar) SET search_path = public;

REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM anon, authenticated, public;

-- RLS optimizado: predicciones
DROP POLICY IF EXISTS "predicciones_por_rol" ON predicciones;
CREATE POLICY "predicciones_por_rol" ON predicciones
  FOR SELECT TO authenticated
  USING (
    ((select auth.jwt())->>'rol') IN ('ANALISTA_SDSCJ','ADMIN','CIUDADANO')
    OR (
      ((select auth.jwt())->>'rol') = 'COMANDANTE_CAI'
      AND upz_cod IN (
        SELECT unnest(cg.upz_codes) FROM cuadrantes_geom cg
        WHERE cg.cuadrante_id = (select auth.jwt())->>'cuadrante_asignado'
      )
    )
  );

-- RLS optimizado y fusionado: user_profiles (una sola política SELECT para authenticated)
DROP POLICY IF EXISTS "perfil_propio" ON user_profiles;
DROP POLICY IF EXISTS "admin_lee_perfiles" ON user_profiles;
CREATE POLICY "perfil_propio_o_admin" ON user_profiles
  FOR SELECT TO authenticated
  USING (
    user_id = (select auth.uid())
    OR ((select auth.jwt())->>'rol') = 'ADMIN'
  );

DROP POLICY IF EXISTS "admin_edita_perfiles" ON user_profiles;
CREATE POLICY "admin_edita_perfiles" ON user_profiles
  FOR UPDATE TO authenticated
  USING (((select auth.jwt())->>'rol') = 'ADMIN');

CREATE INDEX IF NOT EXISTS idx_user_profiles_cuadrante
  ON user_profiles (cuadrante_asignado);
