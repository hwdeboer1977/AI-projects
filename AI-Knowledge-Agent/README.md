# AI‑Knowledge‑Agent

A minimal, production‑ready **Internal Knowledge / Q&A Agent** built with **Node.js, PostgreSQL + pgvector, and OpenAI embeddings**.

The goal of this project is to ingest structured legal / policy documents (web pages, later PDFs & markdown), store them as semantic vectors, and enable accurate **RAG‑based Q&A** over internal knowledge.

---

## ✨ What this project does

- Fetches **policy / legal webpages** (e.g. Stripe, GitHub, OpenAI, Cloudflare)
- Extracts clean text from HTML
- **Chunks** documents into overlapping segments
- Generates **embeddings** using OpenAI
- Stores chunks in **Postgres + pgvector**
- Prepares the foundation for a `/ask` endpoint (RAG)

This is intentionally simple, explicit, and inspectable — no magic frameworks.

---

## 🧱 Architecture (High‑level)

```
Web / Docs / PDFs
        ↓
Text Extraction
        ↓
Chunking (+ overlap)
        ↓
Embeddings (OpenAI)
        ↓
Postgres (pgvector)
        ↓
Semantic Retrieval (RAG)
        ↓
LLM Answer + Sources
```

---

## 📁 Project Structure

```
AI-Knowledge-Agent/
│
├─ docker-compose.yml        # Postgres + pgvector
├─ .env                     # Database + OpenAI config
├─ package.json
├─ sql/
│   └─ schema.sql            # documents / chunks tables
│
├─ src/
│   ├─ db.js                 # pg Pool + helpers
│   │
│   ├─ rag/
│   │   ├─ chunker.js        # text → chunks (+ overlap)
│   │   └─ embedding.js      # OpenAI embeddings
│   │
│   └─ scripts/
│       ├─ ingest_web.js     # Web ingestion pipeline
│       └─ test_db_via_minimal.js  # Test DB
│
│
└─ README.md
```

---

## ⚙️ Prerequisites

- Node.js ≥ 18
- Docker Desktop
- OpenAI API key

---

## 🐳 Postgres + pgvector (Docker)

We run Postgres in Docker to:

- avoid local version conflicts
- guarantee pgvector availability
- keep dev environment reproducible

### Start database

```bash
docker compose up -d
```

Database is exposed on **port 5433** to avoid conflicts with local Postgres.

---

## 🗄️ Database Schema

`sql/schema.sql` creates two core tables:

- **documents** — one row per source (URL, file)
- **chunks** — chunked text + embedding vectors

```sql
documents(id, source, title, created_at)
chunks(id, document_id, chunk_index, content, embedding, metadata)
```

Load schema:

```bash
Get-Content sql/schema.sql | docker exec -i rag_pg psql -U postgres -d ragdb
```

---

## 🔐 Environment Variables

`.env`

```env
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5433/ragdb
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
```

---

## ✅ Verify DB Connection

Minimal sanity check:

```bash
node src/scripts/test_db_minimal.js
```

Expected output:

```
Running minimal DB test...
DB OK: { now: ... }
```

---

## 🌐 Web Ingestion

Edit `src/scripts/ingest_web.js`:

```js
export const URLS = ["https://stripe.com/privacy"];
```

Run:

```bash
node src/scripts/ingest_web.js
```

Check results:

```bash
docker exec -it rag_pg psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM documents;"
docker exec -it rag_pg psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM chunks;"
```

---

## 🧩 Why chunking is required

Chunking is essential for RAG systems:

- LLMs have context limits
- Vector search works on **small semantic units**
- Overlap prevents cutting sentences / definitions

Current strategy:

- ~1600 characters per chunk
- ~200 character overlap

Later improvements:

- Chunk by **headings / sections**
- Add `section_title` metadata (contracts, policies)

---

## 📄 Supported Sources

Currently:

- Web pages (HTML)

Planned:

- Markdown files (`docs/` folder)
- PDFs (policy / contracts)
- Internal docs

All sources share the same pipeline after text extraction.

---

## 🚀 Next Steps

Recommended order:

1. **Build `/ask` endpoint** (RAG Q&A)
2. Ingest all policy URLs
3. Add local docs / PDFs
4. Improve chunking (section‑aware)
5. Add citations + source highlighting

---

## 🎯 Use cases

- Internal compliance assistant
- Legal / policy Q&A
- Security & privacy reviews
- Developer documentation bots
- Regulator / audit tooling prototypes

---

## 🧠 Design Philosophy

- Explicit over magical
- SQL over abstractions
- Inspectable data
- Minimal dependencies

This is a **foundation**, not a black‑box product.

---

## 📜 License

MIT
