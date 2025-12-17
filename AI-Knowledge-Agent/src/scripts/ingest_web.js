import { JSDOM } from "jsdom";
import dotenv from "dotenv";

import { query, toPgVector } from "../db.js";
import { chunkText } from "../rag/chunker.js";
import { embedTexts } from "../rag/embedding.js";

dotenv.config();

export const URLS = [
  "https://stripe.com/privacy",
  // "https://stripe.com/legal/dpa",

  // "https://docs.github.com/en/site-policy/github-terms/github-terms-of-service",
  // "https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies",
  // "https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement",

  // "https://openai.com/policies/terms-of-use/",
  // "https://openai.com/policies/privacy-policy/",
  // "https://openai.com/policies/usage-policies/",

  // "https://www.cloudflare.com/terms/",
  // "https://www.cloudflare.com/privacypolicy/",
  // "https://www.cloudflare.com/cloudflare-customer-dpa/",
];

async function extractTextFromHTML(html) {
  const dom = new JSDOM(html);
  const document = dom.window.document;

  // verwijder rommel
  document
    .querySelectorAll("script, style, nav, footer, header")
    .forEach((e) => e.remove());

  return document.body.textContent.replace(/\s+/g, " ").trim();
}

async function upsertDocument({ source, title }) {
  const res = await query(
    `
    INSERT INTO documents (source, title)
    VALUES ($1, $2)
    ON CONFLICT (source)
    DO UPDATE SET updated_at = now()
    RETURNING id;
    `,
    [source, title]
  );
  return res.rows[0].id;
}

async function clearChunks(documentId) {
  await query(`DELETE FROM chunks WHERE document_id = $1`, [documentId]);
}

async function main() {
  for (const url of URLS) {
    console.log(`Fetching ${url}`);

    const resp = await fetch(url, {
      headers: { "User-Agent": "Internal-QA-RAG/1.0" },
    });

    if (!resp.ok) {
      console.warn(`Failed: ${url}`);
      continue;
    }

    const html = await resp.text();
    const text = await extractTextFromHTML(html);

    if (!text || text.length < 200) {
      console.warn(`Too little content: ${url}`);
      continue;
    }

    const docId = await upsertDocument({
      source: url,
      title: url,
    });

    await clearChunks(docId);

    const chunks = chunkText(text, { maxChars: 1600, overlapChars: 200 });
    const embeddings = await embedTexts(chunks);

    for (let i = 0; i < chunks.length; i++) {
      await query(
        `
        INSERT INTO chunks (document_id, chunk_index, content, embedding, metadata)
        VALUES ($1, $2, $3, $4::vector, $5::jsonb)
        `,
        [
          docId,
          i,
          chunks[i],
          toPgVector(embeddings[i]),
          JSON.stringify({ url }),
        ]
      );
    }

    console.log(`Indexed ${url} (${chunks.length} chunks)`);
  }

  await query(`ANALYZE chunks`);
  console.log("Web ingest done");
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
