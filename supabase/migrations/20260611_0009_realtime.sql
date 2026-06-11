-- SeguroData — Migración 0009: habilitar Supabase Realtime para silver_upz_mes
-- Alternativa Dashboard: Database → Publications → supabase_realtime → toggle silver_upz_mes ON
-- Esta migración hace lo mismo vía SQL para evitar el paso manual.

ALTER PUBLICATION supabase_realtime ADD TABLE silver_upz_mes;
