-- SeguroData — Migración 0001: extensiones
-- PostGIS para geometrías UPZ/cuadrantes; pgvector para embeddings GraphRAG (384 dims)

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
