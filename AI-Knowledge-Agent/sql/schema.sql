-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table (1 row per URL / file)
CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  title TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Needed for ON CONFLICT (source)
CREATE UNIQUE INDEX IF NOT EXISTS documents_source_unique
  ON documents(source);

-- Chunks table (vectorized text)
CREATE TABLE IF NOT EXISTS chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL
    REFERENCES documents(id)
    ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS chunks_doc_chunk_idx
  ON chunks(document_id, chunk_index);
