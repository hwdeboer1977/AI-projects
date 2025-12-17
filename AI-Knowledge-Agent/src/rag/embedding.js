import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function embedTexts(texts) {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("Missing OPENAI_API_KEY in .env");
  }

  const model = process.env.EMBEDDING_MODEL || "text-embedding-3-small";

  const resp = await client.embeddings.create({
    model,
    input: texts,
  });

  return resp.data.map((d) => d.embedding);
}
