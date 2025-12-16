import "dotenv/config";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { chromium } from "playwright";
import TurndownService from "turndown";
import OpenAI from "openai";
import { JSDOM } from "jsdom";
import { Readability } from "@mozilla/readability";
import { fileURLToPath } from "url";

// Original source ref: :contentReference[oaicite:1]{index=1}
// CLI:
// node src/summarize_add.js "https://example.com" --depth long --out ./outputs
// API usage:
// import { summarizeAdd } from "./summarize_add.js";
// const r = await summarizeAdd({ url, depth: "medium" });

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

/* -------------------------------------------------- */
/* Utils                                              */
/* -------------------------------------------------- */

function parseArgs(argv) {
  const args = argv.slice(2);
  let outDir = "./outputs";
  let depth = "medium";
  let noCache = false;
  const urlParts = [];

  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--out" || a === "-o") {
      outDir = args[++i] || outDir;
    } else if (a === "--depth") {
      depth = args[++i] || depth;
    } else if (a === "--no-cache") {
      noCache = true;
    } else {
      urlParts.push(a);
    }
  }

  return { url: urlParts.join(" ").trim(), outDir, depth, noCache };
}

function hash(str) {
  return crypto.createHash("sha1").update(str).digest("hex");
}

function safeFileName(name) {
  return (
    name
      .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
      .slice(0, 120)
      .trim() || "summary"
  );
}

function depthConfig(depth) {
  if (depth === "short") return { bullets: "6–8", tokens: 700 };
  if (depth === "long") return { bullets: "14–18", tokens: 2200 };
  return { bullets: "10–14", tokens: 1400 };
}

/* -------------------------------------------------- */
/* Extraction                                         */
/* -------------------------------------------------- */

async function extractHTML(url) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.waitForTimeout(800);

  const html = await page.content();
  const title = await page.title();
  const finalUrl = page.url();

  await browser.close();
  return { html, title, finalUrl };
}

function readabilityExtract(html, url) {
  const dom = new JSDOM(html, { url });
  const reader = new Readability(dom.window.document);
  const article = reader.parse();
  if (!article || !article.content) return null;
  return article;
}

function htmlToMarkdown(html) {
  const td = new TurndownService({
    headingStyle: "atx",
    codeBlockStyle: "fenced",
  });

  td.addRule("pre", {
    filter: ["pre"],
    replacement: (_, node) =>
      `\n\n\`\`\`\n${node.textContent.trim()}\n\`\`\`\n\n`,
  });

  return td.turndown(html);
}

/* -------------------------------------------------- */
/* Chunking                                           */
/* -------------------------------------------------- */

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

/* -------------------------------------------------- */
/* Summarization                                      */
/* -------------------------------------------------- */

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
`,
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

async function mergeSummaries(url, title, summaries, depth, { model }) {
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
- Math intuition
- Training workflow
- Common pitfalls
- Practical checklist
- Source link

SOURCE: ${url}
TITLE: ${title}

INPUT NOTES:
${summaries.join("\n\n")}
`,
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

/* -------------------------------------------------- */
/* Public API                                         */
/* -------------------------------------------------- */

/**
 * Summarize a URL in "add context" mode.
 *
 * If outDir is provided, files/caches are written (CLI behavior).
 * If outDir is omitted, it returns the result only (API behavior).
 */
export async function summarizeAdd({
  url,
  depth = "medium",
  outDir, // optional (enable file writes)
  noCache = false,
  model = "gpt-4.1-mini",
  chunkSize = 8000,
} = {}) {
  if (!url) throw new Error("Missing url");

  // Setup dirs only if writing outputs
  let cacheDir, htmlPath, mdPath;
  if (outDir) {
    fs.mkdirSync(outDir, { recursive: true });
    cacheDir = path.join(outDir, ".cache");
    fs.mkdirSync(cacheDir, { recursive: true });

    const key = hash(url);
    htmlPath = path.join(cacheDir, `${key}.html`);
    mdPath = path.join(cacheDir, `${key}.md`);
  }

  let html, pageTitle, finalUrl;
  let usedCache = false;

  if (outDir && !noCache && fs.existsSync(htmlPath)) {
    html = fs.readFileSync(htmlPath, "utf8");
    pageTitle = "Cached Page";
    finalUrl = url;
    usedCache = true;
  } else {
    const res = await extractHTML(url);
    html = res.html;
    pageTitle = res.title;
    finalUrl = res.finalUrl;

    if (outDir) fs.writeFileSync(htmlPath, html);
  }

  const article = readabilityExtract(html, finalUrl || url);
  if (!article) throw new Error("Readability extraction failed");

  const extractedMarkdown = htmlToMarkdown(article.content);

  if (outDir) fs.writeFileSync(mdPath, extractedMarkdown);

  const chunks = chunkText(extractedMarkdown, chunkSize);
  const partials = [];
  for (let i = 0; i < chunks.length; i++) {
    partials.push(await summarizeChunk(chunks[i], i + 1, { model }));
  }

  const markdown = await mergeSummaries(
    finalUrl || url,
    article.title || pageTitle,
    partials,
    depth,
    { model }
  );

  // Optional file write (CLI mode)
  let outFile;
  if (outDir) {
    outFile = path.join(outDir, `${safeFileName(article.title)}_add.md`);
    fs.writeFileSync(outFile, markdown, "utf8");
  }

  return {
    mode: "add",
    depth,
    url,
    finalUrl: finalUrl || url,
    title: article.title || pageTitle,
    markdown,
    extractedMarkdown,
    meta: {
      chunks: chunks.length,
      usedCache,
      outFile: outFile || null,
    },
  };
}

/* -------------------------------------------------- */
/* CLI entry                                          */
/* -------------------------------------------------- */

const isDirectRun =
  process.argv[1] &&
  fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isDirectRun) {
  (async () => {
    const { url, outDir, depth, noCache } = parseArgs(process.argv);
    if (!url) {
      console.error(
        'Usage: node summarize_add.js "<url>" [--depth short|medium|long] [--out ./outputs] [--no-cache]'
      );
      process.exit(1);
    }

    try {
      const r = await summarizeAdd({ url, depth, outDir, noCache });
      console.log("\nDone:");
      console.log(r.meta.outFile || "(no file written)");
    } catch (e) {
      console.error("Error:", e.message);
      process.exit(1);
    }
  })();
}
