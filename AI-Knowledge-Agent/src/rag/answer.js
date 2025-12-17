import dotenv from "dotenv";
import OpenAI from "openai";
import { retrieveTopK } from "./retriever.js";

dotenv.config();

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

function buildContext(chunks) {
  return chunks
    .map((c, i) => {
      const src = c.metadata?.url || c.source || "unknown";
      return `[#${i + 1}] Source: ${src}\n${c.content}`;
    })
    .join("\n\n---\n\n");
}

export async function answerQuestion(question, { topK = 6 } = {}) {
  console.log("ASK:", question);

  const chunks = await retrieveTopK(question, { topK });
  console.log("Retrieved chunks:", chunks.length);

  const context = buildContext(chunks);

  const model = process.env.CHAT_MODEL || "gpt-4.1-mini";
  console.log("Calling OpenAI:", model);

  const completion = await client.chat.completions.create({
    model,
    temperature: 0.2,
    messages: [
      {
        role: "system",
        content:
          "Answer ONLY using the provided context. If insufficient, say you don't know. " +
          "Add citations like [#1], [#2] referring to the chunk numbers.",
      },
      {
        role: "user",
        content: `Question:\n${question}\n\nContext:\n${context}`,
      },
    ],
  });

  console.log("OpenAI responded");

  const answer = completion.choices?.[0]?.message?.content?.trim() || "";

  const sources = chunks.map((c, i) => ({
    ref: `#${i + 1}`,
    source: c.metadata?.url || c.source,
    title: c.title,
    chunk_index: c.chunk_index,
    distance: Number(c.distance),
  }));

  return { answer, sources };
}
