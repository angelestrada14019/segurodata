-- SeguroData — Migración 0005: perfiles de usuario + autoprovisioning + hook de claims
-- 4 roles: CIUDADANO · COMANDANTE_CAI · ANALISTA_SDSCJ · ADMIN.
-- Autoprovisioning por dominio de email (trigger sobre auth.users).
-- custom_access_token_hook inyecta `rol` y `cuadrante_asignado` en el JWT.
-- ⚠️ PASO MANUAL post-migración: habilitar el hook en Dashboard → Auth → Hooks → Custom Access Token.

CREATE TABLE IF NOT EXISTS user_profiles (
  user_id            uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email              varchar NOT NULL,
  rol                varchar NOT NULL DEFAULT 'CIUDADANO'
                     CHECK (rol IN ('CIUDADANO','COMANDANTE_CAI','ANALISTA_SDSCJ','ADMIN')),
  cuadrante_asignado varchar REFERENCES cuadrantes_geom(cuadrante_id),
  aprobado           boolean NOT NULL DEFAULT false,
  created_at         timestamptz NOT NULL DEFAULT now()
);

-- Autoprovisioning por dominio de email
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rol text := 'CIUDADANO';
  v_aprobado boolean := false;
BEGIN
  IF NEW.email ILIKE '%@policia.gov.co' THEN
    v_rol := 'COMANDANTE_CAI'; v_aprobado := true;   -- cuadrante_asignado lo fija ADMIN después
  ELSIF NEW.email ILIKE '%@sdscj.gov.co' THEN
    v_rol := 'ANALISTA_SDSCJ'; v_aprobado := true;
  END IF;
  INSERT INTO public.user_profiles (user_id, email, rol, aprobado)
  VALUES (NEW.id, NEW.email, v_rol, v_aprobado)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Hook de claims custom (rol + cuadrante_asignado en el access token)
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  claims jsonb;
  v_rol text;
  v_cuadrante text;
BEGIN
  SELECT rol, cuadrante_asignado INTO v_rol, v_cuadrante
  FROM public.user_profiles
  WHERE user_id = (event->>'user_id')::uuid;

  claims := COALESCE(event->'claims', '{}'::jsonb);
  claims := jsonb_set(claims, '{rol}', to_jsonb(COALESCE(v_rol, 'CIUDADANO')));
  IF v_cuadrante IS NOT NULL THEN
    claims := jsonb_set(claims, '{cuadrante_asignado}', to_jsonb(v_cuadrante));
  ELSE
    claims := jsonb_set(claims, '{cuadrante_asignado}', 'null'::jsonb);
  END IF;
  RETURN jsonb_set(event, '{claims}', claims);
END;
$$;

-- Permisos requeridos por Supabase Auth para ejecutar el hook
GRANT USAGE ON SCHEMA public TO supabase_auth_admin;
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook FROM authenticated, anon, public;
GRANT SELECT ON TABLE public.user_profiles TO supabase_auth_admin;
