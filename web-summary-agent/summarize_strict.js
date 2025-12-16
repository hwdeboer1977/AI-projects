import "dotenv/config";
import fs from "fs";
import path from "path";
import crypto from "crypto";
import { chromium } from "playwright";
import TurndownService from "turndown";
import OpenAI from "openai";
import { JSDOM } from "jsdom";
import { Readability } from "@mozilla/readability";

// TO RUN:
// node summarize_strict.js "https://developers.google.com/machine-learning/crash-course/linear-regression" --depth long

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

/* -------------------------------------------------- */
/* CLI + utils                                        */
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

function depthConfig(depth) {
  if (depth === "short") return { bullets: "6–8", tokens: 700 };
  if (depth === "long") return { bullets: "14–18", tokens: 2200 };
  return { bullets: "10–14", tokens: 1400 };
}

async function summarizeChunk(chunk, idx) {
  const resp = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
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

async function mergeSummaries(url, title, summaries) {
  const resp = await openai.chat.completions.create({
    model: "gpt-4.1-mini",
    temperature: 0.1,
    max_tokens: 1400,
    messages: [
      {
        role: "system",
        content: `
You are a strict technical summarizer.

HARD RULES (must follow):
- Only include facts, explanations, definitions, and equations that are explicitly present in the provided text.
- Do NOT add general machine learning knowledge.
- Do NOT infer or extend concepts beyond what is written.
- If an expected concept is not covered in the text, explicitly write: "Not covered on this page."
- If the text is vague, remain vague — do not clarify from prior knowledge.
- Do NOT add examples unless the text includes them.
- Faithfulness to the source is more important than completeness.
        `.trim(),
      },
      {
        role: "user",
        content: `
Create a README-style summary of the following lesson.

Required structure:
- # Title
- Overview (only what the text states)
- Key points (bullet list, factual only)
- Core concepts & definitions (only if defined in text)
- Mathematical formulation (only equations explicitly mentioned; otherwise say "Not covered on this page")
- Notes / limitations mentioned in the text (if any)
- Source

Do NOT include:
- Practical checklists
- Common pitfalls
- Best practices
- Training workflows
- External context

SOURCE URL:
${url}

PAGE TITLE:
${title}

EXTRACTED NOTES (from the page only):
${summaries.join("\n\n")}
        `.trim(),
      },
    ],
  });

  return resp.choices[0].message.content.trim();
}

/* -------------------------------------------------- */
/* Main                                               */
/* -------------------------------------------------- */

async function main() {
  const { url, outDir, depth, noCache } = parseArgs(process.argv);
  if (!url) {
    console.error(
      'Usage: node summarize.js "<url>" [--depth short|medium|long]'
    );
    process.exit(1);
  }

  fs.mkdirSync(outDir, { recursive: true });
  const cacheDir = path.join(outDir, ".cache");
  fs.mkdirSync(cacheDir, { recursive: true });

  const key = hash(url);
  const htmlPath = path.join(cacheDir, `${key}.html`);
  const mdPath = path.join(cacheDir, `${key}.md`);

  let html, title;

  if (!noCache && fs.existsSync(htmlPath)) {
    html = fs.readFileSync(htmlPath, "utf8");
    title = "Cached Page";
  } else {
    console.log("1) Fetching page…");
    const res = await extractHTML(url);
    html = res.html;
    title = res.title;
    fs.writeFileSync(htmlPath, html);
  }

  console.log("2) Extracting readable content…");
  const article = readabilityExtract(html, url);
  if (!article) throw new Error("Readability extraction failed");

  const markdown = htmlToMarkdown(article.content);
  fs.writeFileSync(mdPath, markdown);

  console.log("3) Chunk summarization…");
  const chunks = chunkText(markdown);
  const partials = [];
  for (let i = 0; i < chunks.length; i++) {
    partials.push(await summarizeChunk(chunks[i], i + 1));
  }

  console.log("4) Final merge…");
  const finalSummary = await mergeSummaries(
    url,
    article.title,
    partials,
    depth
  );

  const outFile = path.join(outDir, `${safeFileName(article.title)}_strict.md`);
  fs.writeFileSync(outFile, finalSummary, "utf8");

  console.log("\nDone:");
  console.log(outFile);
}

main().catch((e) => {
  console.error("Error:", e.message);
  process.exit(1);
});
