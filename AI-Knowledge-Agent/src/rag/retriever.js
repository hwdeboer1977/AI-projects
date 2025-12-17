import { query, toPgVector } from "../db.js";
import { embedTexts } from "./embedding.js";

export async function retrieveTopK(question, { topK = 6 } = {}) {
  const [qEmbedding] = await embedTexts([question]);

  const res = await query(
    `
    SELECT
      d.id AS document_id,
      d.source,
      d.title,
      c.chunk_index,
      c.content,
      c.metadata,
      (c.embedding <=> $1::vector) AS distance
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    ORDER BY c.embedding <=> $1::vector
    LIMIT $2;
    `,
    [toPgVector(qEmbedding), topK]
  );

  return res.rows;
}
