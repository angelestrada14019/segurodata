-- SeguroData — Migración 0004: corpus GraphRAG (pgvector)
-- Embeddings all-MiniLM-L6-v2 (384 dims). Índice HNSW (mejor recall que IVFFLAT
-- en corpus pequeño, sin necesidad de entrenar listas). RPC match_documents con
-- firma exacta consumida por backend/app/repositories/documents_repo.py.

CREATE TABLE IF NOT EXISTS documents_corpus (
  id           bigserial PRIMARY KEY,
  content      text NOT NULL,
  content_hash varchar UNIQUE,
  source       varchar NOT NULL,
  titulo       varchar,
  fecha        date,
  url          varchar,
  upz_cod      varchar,
  embedding    vector(384) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents_corpus
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_upz varchar DEFAULT NULL
)
RETURNS TABLE (
  id bigint, content text, source varchar, titulo varchar,
  fecha date, url varchar, similarity float
)
LANGUAGE sql STABLE AS $$
  SELECT dc.id, dc.content, dc.source, dc.titulo, dc.fecha, dc.url,
         1 - (dc.embedding <=> query_embedding) AS similarity
  FROM documents_corpus dc
  WHERE (filter_upz IS NULL OR dc.upz_cod = filter_upz)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
$$;
