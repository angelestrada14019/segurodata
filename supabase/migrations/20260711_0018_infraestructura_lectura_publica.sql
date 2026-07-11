-- Migración 0018: F8/F13/F14 (TransMilenio, Cámaras Salvavidas, Alumbrado)
-- pasan de authenticated-only a lectura pública (anon + authenticated).
--
-- Razón: a diferencia de cuadrantes_geom (expone nombre de CAI + teléfono,
-- decisión previa a esta migración que se mantiene intacta), estas 3 fuentes
-- son datos de infraestructura 100% públicos que cualquiera puede descargar
-- sin cuenta desde los portales de datos abiertos de origen (ArcGIS Hub SDM,
-- Catastro Bogotá, GIS TransMilenio) — restringirlas en el mapa no aportaba
-- ninguna protección real, solo bloqueaba silenciosamente al visitante
-- público del Módulo 1, que se anuncia como "acceso público de solo
-- lectura" (ver wiki_pages/Modulos.md). Decisión confirmada explícitamente
-- por el usuario — cuadrantes_geojson NO se toca en esta migración.

DROP POLICY IF EXISTS "transmilenio_autenticados" ON transmilenio_geom;
CREATE POLICY "transmilenio_lectura_publica" ON transmilenio_geom
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "camaras_autenticados" ON camaras_geom;
CREATE POLICY "camaras_lectura_publica" ON camaras_geom
  FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "upz_infraestructura_autenticados" ON upz_infraestructura;
CREATE POLICY "upz_infraestructura_lectura_publica" ON upz_infraestructura
  FOR SELECT TO anon, authenticated USING (true);

GRANT EXECUTE ON FUNCTION public.transmilenio_geojson TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.camaras_geojson TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.alumbrado_geojson TO anon, authenticated;
