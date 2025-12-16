import "dotenv/config";
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const ALLOWED_MODES = new Set(["strict", "add"]);
const ALLOWED_DEPTHS = new Set(["short", "medium", "long"]);

function depthConfig(depth) {
  if (depth === "short") return { tokens: 700, bullets: "6–8" };
  if (depth === "long") return { tokens: 2200, bullets: "14–18" };
  return { tokens: 1400, bullets: "10–14" };
}

function chunkText(text, size = 8000) {
  const chunks = [];
  let current = "";
  for (const line of text.split("\n")) {
    if ((current + line).length > size) {
      chunks.push(current);
      current = "";
    }
    current += line + "\n";
  }
  if (current.trim()) chunks.push(current);
  return chunks;
}

async function summarizeChunk(chunk, idx, { model }) {
  const resp = await openai.chat.completions.create({
    model,
    temperature: 0.2,
    max_tokens: 700,
    messages: [
      { role: "system", content: "Summarize technical text accurately." },
      {
        role: "user",
        content: `
Summarize this section into concise bullet notes.
Focus on facts, definitions, and explanations.

SECTION ${idx}:
${chunk}
`.trim(),
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

async function mergeStrict({ url, title, notes, depth, model }) {
  const cfg = depthConfig(depth);

  const resp = await openai.chat.completions.create({
    model,
    temperature: 0.1,
    max_tokens: cfg.tokens,
    messages: [
      {
        role: "system",
        content: `
You are a strict technical summarizer.

HARD RULES:
- Only include information explicitly present in the provided text.
- Do NOT add background knowledge or inferences.
- If something is not covered, say: "Not covered in provided content."
`.trim(),
      },
      {
        role: "user",
        content: `
Create a README-style strict summary.

Structure:
- # Title
- Overview (only what text states)
- Key points (bullets, factual only)
- Core concepts & definitions (only if defined)
- Mathematical formulation (only if present; else "Not covered in provided content.")
- Notes / limitations mentioned
- Source

SOURCE URL: ${url || "Not provided"}
TITLE: ${title || "Untitled"}

CONTENT NOTES:
${notes.join("\n\n")}
`.trim(),
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

async function mergeAdd({ url, title, notes, depth, model }) {
  const cfg = depthConfig(depth);

  const resp = await openai.chat.completions.create({
    model,
    temperature: 0.2,
    max_tokens: cfg.tokens,
    messages: [
      {
        role: "system",
        content: "You write clean, structured README-style study notes.",
      },
      {
        role: "user",
        content: `
Create a detailed README-style summary.

Requirements:
- Title
- Overview paragraph
- Key ideas (${cfg.bullets} bullets)
- Core concepts (definitions)
- Practical checklist
- Source link

SOURCE: ${url || "Not provided"}
TITLE: ${title || "Untitled"}

INPUT NOTES:
${notes.join("\n\n")}
`.trim(),
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

/**
 * Summarize provided text (no browsing).
 * Perfect for browser extension / side panel.
 */
export async function summarizeText({
  content,
  title = "",
  url = "",
  mode = "strict",
  depth = "medium",
  model = "gpt-4.1-mini",
  chunkSize = 8000,
} = {}) {
  if (!content || typeof content !== "string")
    throw new Error("content is required");
  if (!ALLOWED_MODES.has(mode)) throw new Error(`Invalid mode: ${mode}`);
  if (!ALLOWED_DEPTHS.has(depth)) throw new Error(`Invalid depth: ${depth}`);

  const chunks = chunkText(content, chunkSize);

  const partials = [];
  for (let i = 0; i < chunks.length; i++) {
    partials.push(await summarizeChunk(chunks[i], i + 1, { model }));
  }

  const markdown =
    mode === "add"
      ? await mergeAdd({ url, title, notes: partials, depth, model })
      : await mergeStrict({ url, title, notes: partials, depth, model });

  return {
    mode,
    depth,
    url,
    title,
    markdown,
    meta: {
      chunks: chunks.length,
      inputChars: content.length,
    },
  };
}
