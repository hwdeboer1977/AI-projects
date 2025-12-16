# Web Page Summarization Agent (WIP)

This project is an experimental **AI-powered web page summarization agent**.
It fetches a web page, extracts the readable content, and generates a structured summary using an LLM.

The project is currently **CLI-based** and serves as the foundation for a future:

- backend API
- web app (paste URL → summary)
- browser extension (summarize the page you are reading)

---

## Current Status

✅ CLI tool that summarizes a **single web page**  
✅ Uses **Playwright + Readability** for robust content extraction  
✅ Supports **long documents via chunking (map → reduce)**  
✅ Supports **multiple summary styles**  
✅ Explicit handling of **LLM hallucination** via a strict, grounded mode

🚧 Backend API not yet finalized  
🚧 Web UI not yet built  
🚧 Browser extension not yet built

---

## Implemented Scripts

### 1. `summarize_add.js` — Exploratory / Enriched Summary

This script generates **rich, study-note style summaries**.

**Characteristics**

- Chunk-based summarization
- Encourages structured output:
  - overview
  - key ideas
  - core concepts
  - math intuition
  - training workflow
  - pitfalls & checklist
- Optimized for learning and exploration
- May include **general background knowledge** beyond the page itself

**Use case**

- Studying technical topics
- Creating learning notes
- When completeness is preferred over strict faithfulness

**Run**

```bash
node summarize_add.js "<url>" --depth long
```

---

### 2. `summarize_strict.js` — Grounded / Faithful Summary

This script generates **strict, source-grounded summaries**.

**Characteristics**

- Chunk-based summarization
- Enforces hard constraints:
  - only include information explicitly present in the source page
  - no inferred explanations
  - no external or background ML knowledge
  - missing concepts are explicitly marked as:
    **"Not covered on this page."**
- Removes sections that invite hallucination:
  - no best practices
  - no workflows
  - no pitfalls unless explicitly mentioned

**Use case**

- Documentation
- Research and academic summaries
- Regulatory or compliance-oriented analysis
- Verifying what a page _actually states_

**Run**

```bash
node summarize_strict.js "<url>" --depth long
```

---

## Core Architecture (CLI)

```
URL
 ↓
Playwright (fetch & render)
 ↓
Readability (extract main content)
 ↓
HTML → Markdown
 ↓
Chunking
 ↓
LLM summarization (map)
 ↓
LLM merge (reduce)
 ↓
Markdown output
```

---

## Key Design Decisions

### Grounded vs Enriched Summaries

Two modes exist intentionally:

| Mode     | Goal                                 |
| -------- | ------------------------------------ |
| `add`    | Helpful, learning-oriented summaries |
| `strict` | Faithful, source-only summaries      |

This explicit separation avoids prompt ambiguity and makes summarization behavior predictable.

---

## What This Project Is **Not** (Yet)

- ❌ Not a backend API
- ❌ Not a multi-page course crawler
- ❌ Not a browser extension
- ❌ Not summarizing video or audio content

---

## Planned Next Steps

### Phase 1 — Backend API

- `POST /v1/summarize/url`
- `POST /v1/summarize/text`
- Rate limiting and SSRF protection
- Grounded mode as default behavior

### Phase 2 — Web App

- Paste URL → summary
- Export as Markdown / PDF

### Phase 3 — Browser Extension

- Side panel UI
- Summarize current page
- Uses backend `/summarize/text`

---

## Tech Stack (Current)

- Node.js (ESM)
- Playwright
- Mozilla Readability
- JSDOM
- Turndown (HTML → Markdown)
- OpenAI API

---
