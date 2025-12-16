# Web Page Summarization Agent

This project is an experimental **AI-powered web page summarization agent**.

It can:

- summarize a web page by URL (server-side fetching), or
- summarize the _currently open page_ directly from the browser (extension)

Readable content is extracted and converted into structured **Markdown summaries** using an LLM.  
The system is designed around **explicit summarization modes** to control hallucination vs enrichment.

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
- Browser Extension (MVP):
  - Chrome MV3 side panel
  - Summarize **current page**
  - Uses `/v1/summarize/text`
  - Markdown preview + copy
- Robust content extraction:
  - Playwright + Readability (backend)
  - DOM-based extraction (extension, MVP)
- Long-document support via chunking (map → reduce)
- Explicit handling of hallucination via a strict, grounded mode

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
│   ├── frontend/              # Web UI (static)
│   │   ├── index.html
│   │   ├── app.js
│   │   └── styles.css
│   │
│   └── extension/             # Chrome Extension (MV3)
│       ├── manifest.json
│       ├── service_worker.js
│       ├── sidepanel.html
│       ├── sidepanel.js
│       ├── sidepanel.css
│       └── marked.min.js
│
├── src/scripts/
│   └── copy-marked.js          # Copies marked into extension automatically
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
- Missing concepts are explicitly marked as: **“Not covered on this page.”**

**CLI usage**

```bash
node src/tools/summarize_strict.js "<url>" --depth long
```

---

### 2. `summarize_add.js` — Enriched / Exploratory Summary (URL input)

**Characteristics**

- Study-note style summaries
- Structured output (overview, key ideas, concepts, workflows)
- May include general background knowledge

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
- Used by the browser extension and copy/paste workflows

---

## Backend API

### Start backend

```bash
npm run server
```

Default port: `http://localhost:4000`

---

### `POST /v1/summarize/url`

```json
{
  "url": "https://example.com",
  "mode": "strict",
  "depth": "medium"
}
```

---

### `POST /v1/summarize/text`

```json
{
  "title": "Optional title",
  "url": "Optional source URL",
  "mode": "add",
  "depth": "short",
  "content": "Raw text to summarize..."
}
```

---

## Web UI (MVP)

### Start frontend

```bash
npx http-server ./src/frontend -p 5173
```

Open:

```
http://localhost:5173/index.html
```

---

## Browser Extension (MVP)

### Features

- Chrome Manifest V3 side panel
- Summarize the **currently open page**
- Markdown preview and copy
- Uses backend `/v1/summarize/text`

### Permissions

The extension uses:

```json
"permissions": ["sidePanel", "activeTab", "scripting"],
"host_permissions": ["<all_urls>"]
```

This is required to extract page content across different sites.

### Load extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `src/extension/`
5. Make sure backend is running

---

## Markdown Support in Extension

- Markdown is rendered using **marked**
- `marked` is bundled locally into the extension
- Automatically copied via:

```bash
npm install
```

(using `src/scripts/copy-marked.js`)

This avoids CSP issues with remote CDNs.

---

## Core Architecture

### URL-based summarization

```
URL → Playwright → Readability → Markdown → Chunking → LLM → Markdown
```

### Text-based summarization

```
DOM/Text → Chunking → LLM → Markdown
```

---

## What This Project Is Not

- ❌ Not a crawler
- ❌ Not a search engine
- ❌ Not production-hardened (auth, billing, quotas)

---

## Tech Stack

- Node.js (ESM)
- Express
- Playwright
- Mozilla Readability
- JSDOM
- Turndown
- Marked (bundled locally)
- OpenAI API
