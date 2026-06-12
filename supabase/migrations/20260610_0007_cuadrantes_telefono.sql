-- SeguroData — Migración 0007: teléfono del CAI en cuadrantes
-- F4 trae PCUTELEFON — lo expone /prescribe en la respuesta (contacto operacional).

ALTER TABLE cuadrantes_geom ADD COLUMN IF NOT EXISTS telefono varchar;
