-- SeguroData — Migración 0010: RPCs helper para seed_supabase.py (REST API, sin DB directa)
-- Permite correr seed_supabase.py solo con SUPABASE_URL + SUPABASE_SERVICE_KEY.

-- Truncar silver antes del bulk insert (bigserial sin key natural — no se puede upsert)
CREATE OR REPLACE FUNCTION public.truncate_silver()
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN TRUNCATE silver_upz_mes; END;
$$;
GRANT EXECUTE ON FUNCTION public.truncate_silver TO service_role;
REVOKE EXECUTE ON FUNCTION public.truncate_silver FROM authenticated, anon, public;

-- Upsert geometría UPZ desde WKT (PostgREST no acepta tipo geometry directamente)
CREATE OR REPLACE FUNCTION public.upsert_upz_geom(
  p_upz_cod text, p_upz_nombre text, p_wkt text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO upz_geometrias (upz_cod, upz_nombre, geom)
  VALUES (p_upz_cod, p_upz_nombre, ST_Multi(ST_GeomFromText(p_wkt, 4326)))
  ON CONFLICT (upz_cod) DO UPDATE
    SET geom = EXCLUDED.geom, upz_nombre = EXCLUDED.upz_nombre;
END;
$$;
GRANT EXECUTE ON FUNCTION public.upsert_upz_geom TO service_role;
REVOKE EXECUTE ON FUNCTION public.upsert_upz_geom FROM authenticated, anon, public;

-- Upsert geometría cuadrante desde WKT
CREATE OR REPLACE FUNCTION public.upsert_cuadrante_geom(
  p_cuadrante_id text, p_nom_cai text, p_telefono text, p_upz_codes text[], p_wkt text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO cuadrantes_geom (cuadrante_id, nom_cai, telefono, upz_codes, geom)
  VALUES (p_cuadrante_id, p_nom_cai, p_telefono, p_upz_codes,
          ST_Multi(ST_GeomFromText(p_wkt, 4326)))
  ON CONFLICT (cuadrante_id) DO UPDATE
    SET geom       = EXCLUDED.geom,
        upz_codes  = EXCLUDED.upz_codes,
        nom_cai    = EXCLUDED.nom_cai,
        telefono   = EXCLUDED.telefono;
END;
$$;
GRANT EXECUTE ON FUNCTION public.upsert_cuadrante_geom TO service_role;
REVOKE EXECUTE ON FUNCTION public.upsert_cuadrante_geom FROM authenticated, anon, public;

-- Regenerar datos sintéticos seed_dev (predicciones + SHAP) directamente en DB
CREATE OR REPLACE FUNCTION public.regenerate_seed_dev()
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE np_ int; ns int;
BEGIN
  DELETE FROM shap_values  WHERE origen = 'seed_dev';
  DELETE FROM predicciones WHERE origen = 'seed_dev';

  WITH crimen AS (
    SELECT upz_cod, anio, mes, sum(n_delitos) AS n
    FROM silver_upz_mes WHERE es_crimen GROUP BY 1, 2, 3
  ),
  s AS (
    SELECT g.upz_cod, coalesce(avg(c.n), 1.0) AS media
    FROM upz_geometrias g LEFT JOIN crimen c ON c.upz_cod = g.upz_cod
    GROUP BY g.upz_cod
  ),
  months AS (
    SELECT 2025 AS anio, m AS mes FROM generate_series(7, 12) m
    UNION ALL SELECT 2026, m FROM generate_series(1, 12) m
  ),
  base AS (
    SELECT s.upz_cod, mo.anio, mo.mes,
           s.media * (0.8 + 0.4 *
             (abs(hashtext(s.upz_cod || '-' || mo.anio || '-' || mo.mes)) % 1000) / 1000.0
           ) AS score
    FROM s CROSS JOIN months mo
  ),
  ranked AS (
    SELECT *, percent_rank() OVER (PARTITION BY anio, mes ORDER BY score) AS pr FROM base
  ),
  probs AS (
    SELECT upz_cod, anio, mes, pr,
      exp(-power(pr - 0.975, 2) / (2 * power(0.13, 2))) AS wc,
      exp(-power(pr - 0.850, 2) / (2 * power(0.13, 2))) AS wa,
      exp(-power(pr - 0.575, 2) / (2 * power(0.16, 2))) AS wm,
      exp(-power(pr - 0.200, 2) / (2 * power(0.20, 2))) AS wb
    FROM ranked
  )
  INSERT INTO predicciones
    (upz_cod, anio, mes, nivel_riesgo, prob_critico, prob_alto, prob_medio, prob_bajo, origen)
  SELECT upz_cod, anio, mes,
    CASE WHEN pr >= 0.95 THEN 'CRITICO' WHEN pr >= 0.75 THEN 'ALTO'
         WHEN pr >= 0.40 THEN 'MEDIO'   ELSE 'BAJO' END,
    wc/(wc+wa+wm+wb), wa/(wc+wa+wm+wb), wm/(wc+wa+wm+wb), wb/(wc+wa+wm+wb),
    'seed_dev'
  FROM probs;

  WITH feats(feature, sesgo) AS (VALUES
    ('n_delitos_upz_4sem',    0.18::float),
    ('cuadrantes_por_km2',    0.12::float),
    ('estrato_promedio_upz',  0.06::float),
    ('luminarias_led_upz',    0.08::float),
    ('n_camaras_upz',         0.05::float),
    ('ratio_nuse_criminal_upz', 0.07::float),
    ('temperatura_c',         0.02::float),
    ('dist_tm_metros',        0.03::float)
  ),
  r AS (
    SELECT upz_cod, anio, mes,
      CASE nivel_riesgo WHEN 'CRITICO' THEN 1.0 WHEN 'ALTO' THEN 0.7
           WHEN 'MEDIO' THEN 0.4 ELSE 0.2 END AS amp
    FROM predicciones WHERE origen = 'seed_dev'
  )
  INSERT INTO shap_values (upz_cod, anio, mes, feature, valor, origen)
  SELECT r.upz_cod, r.anio, r.mes, f.feature,
    round((((abs(hashtext(r.upz_cod || r.anio::text || r.mes::text || f.feature)) % 2000)
      / 1000.0 - 1.0) * r.amp * 0.35 + f.sesgo * r.amp)::numeric, 4),
    'seed_dev'
  FROM r CROSS JOIN feats f;

  SELECT count(*) INTO np_ FROM predicciones WHERE origen = 'seed_dev';
  SELECT count(*) INTO ns  FROM shap_values  WHERE origen = 'seed_dev';
  RETURN jsonb_build_object('predicciones', np_, 'shap_values', ns);
END;
$$;
GRANT EXECUTE ON FUNCTION public.regenerate_seed_dev TO service_role;
REVOKE EXECUTE ON FUNCTION public.regenerate_seed_dev FROM authenticated, anon, public;
