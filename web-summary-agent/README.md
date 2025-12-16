# Web Page Summarization Agent

This project is an experimental **AI-powered web page summarization agent**.

It fetches a web page (or accepts raw text), extracts the readable content, and generates a structured summary using an LLM.  
The system is designed around **explicit summarization modes** to control hallucination vs enrichment.

The project consists of:

- reusable summarization tools
- a backend API
- a minimal web UI
- a foundation for a future browser extension

---

## Current Status

### ✅ Implemented

- CLI tools for summarizing a single web page
- Backend API with two endpoints:
  - `POST /v1/summarize/url`
  - `POST /v1/summarize/text`
- Web UI (MVP):
  - paste URL → summary
  - strict / add mode toggle
  - depth control
  - markdown preview + copy
- Robust content extraction:
  - Playwright + Readability
- Long-document support via chunking (map → reduce)
- Explicit handling of hallucination via a strict, grounded mode

### 🚧 Planned

- Browser extension (side panel)
- In-browser text extraction (Readability)
- Auth / API keys (optional, later)
- PDF export

---

## Project Structure

```
web-summary-agent/
│
├── src/
│   ├── tools/                 # Pure summarization logic
│   │   ├── summarize_add.js
│   │   ├── summarize_strict.js
│   │   └── summarize_text.js
│   │
│   ├── backend/               # Backend API
│   │   └── index.js
│   │
│   └── frontend/              # Web UI (static)
│       ├── index.html
│       ├── app.js
│       └── styles.css
│
├── outputs/                   # CLI outputs only
├── .env
├── package.json
└── README.md
```

---

## Summarization Modes

Two modes exist intentionally:

| Mode     | Behavior                                                               |
| -------- | ---------------------------------------------------------------------- |
| `strict` | Faithful, source-only summary. No external knowledge, no inference.    |
| `add`    | Enriched, learning-oriented summary. May add context and explanations. |

This explicit separation avoids prompt ambiguity and makes summarization behavior predictable.

---

## Implemented Tools

### 1. `summarize_strict.js` — Grounded / Faithful Summary (URL input)

**Characteristics**

- Only includes information explicitly present on the page
- No inferred explanations
- No background ML knowledge
- Missing concepts are explicitly marked as:  
  **“Not covered on this page.”**

**Use cases**

- Documentation
- Research & academic summaries
- Regulatory or compliance-oriented analysis

**CLI usage**

```bash
node src/tools/summarize_strict.js "<url>" --depth long
```

---

### 2. `summarize_add.js` — Enriched / Exploratory Summary (URL input)

**Characteristics**

- Study-note style summaries
- Structured output:
  - overview
  - key ideas
  - core concepts
  - math intuition
  - workflows
  - pitfalls & checklist
- May include general background knowledge

**Use cases**

- Learning technical topics
- Creating study notes
- Exploratory reading

**CLI usage**

```bash
node src/tools/summarize_add.js "<url>" --depth long
```

---

### 3. `summarize_text.js` — Text-Based Summary (No browsing)

**Characteristics**

- Accepts raw text instead of a URL
- No Playwright, no fetching
- Supports both `strict` and `add` modes
- Designed for browser extension and copy/paste use cases

**Use cases**

- Browser extension
- Logged-in pages
- Paywalled content
- Internal dashboards
- Future PDF / document support

---

## Backend API

### Start backend

```bash
node src/backend/index.js
```

Default port: `http://localhost:4000`

---

### `POST /v1/summarize/url`

Summarize a web page by URL.

**Request**

```json
{
  "url": "https://example.com",
  "mode": "strict",
  "depth": "medium"
}
```

**Response**

```json
{
  "ok": true,
  "mode": "strict",
  "depth": "medium",
  "title": "...",
  "finalUrl": "...",
  "markdown": "...",
  "meta": { "chunks": 3 }
}
```

---

### `POST /v1/summarize/text`

Summarize provided text (no browsing).

**Request**

```json
{
  "title": "Optional title",
  "url": "Optional source URL",
  "mode": "add",
  "depth": "short",
  "content": "Raw text to summarize..."
}
```

**Response**

```json
{
  "ok": true,
  "mode": "add",
  "depth": "short",
  "markdown": "...",
  "meta": { "chunks": 2 }
}
```

---

## Web UI (MVP)

The web UI is a lightweight static frontend.

### Start frontend

```bash
npx http-server ./src/frontend -p 5173
```

Open:

```
http://localhost:5173/index.html
```

**Features**

- Paste URL
- Toggle `strict` / `add`
- Choose summary depth
- Markdown preview
- Copy markdown to clipboard

---

## Core Architecture

### URL-based summarization

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

### Text-based summarization

```
Raw text
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

## What This Project Is Not (Yet)

- ❌ Not a multi-page crawler
- ❌ Not a course-wide summarizer
- ❌ Not summarizing video or audio
- ❌ Not production-hardened (auth, billing, quotas)

---

## Next Steps

### Phase 4 — Browser Extension

- Side panel UI
- Summarize current page
- Uses `/v1/summarize/text`

---

## Tech Stack

- Node.js (ESM)
- Playwright
- Mozilla Readability
- JSDOM
- Turndown (HTML → Markdown)
- OpenAI API
