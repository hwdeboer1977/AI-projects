# AI‑Knowledge‑Agent

A **minimal full‑stack RAG (Retrieval‑Augmented Generation) knowledge agent**.

It ingests legal / policy documents (web today, PDFs & markdown later), stores them as embeddings in **PostgreSQL + pgvector**, and exposes a clean **/ask API** with a simple **Next.js frontend**.

This project is intentionally explicit and debuggable — no heavy frameworks, no magic abstractions.

---

## ✨ What this project does

- Ingests **web‑based legal / policy documents** (Stripe, GitHub, OpenAI, Cloudflare)
- Cleans and extracts readable text from HTML
- **Chunks** text into overlapping segments
- Generates **OpenAI embeddings**
- Stores everything in **Postgres + pgvector**
- Performs **semantic retrieval**
- Answers questions using **RAG** with citations
- Provides:
  - REST API (`/ask`)
  - Simple **Next.js frontend**

---

## 🧱 High‑level architecture

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
Retriever (top‑K vectors)
        ↓
LLM Answer + Sources
        ↓
API (/ask) + Next.js UI
```

---

## 📁 Project structure

```
AI-Knowledge-Agent/
│
├─ docker-compose.yml        # Postgres + pgvector (Docker)
├─ .env                     # Backend secrets (NOT committed)
├─ .gitignore
├─ package.json             # Backend scripts
│
├─ sql/
│   └─ schema.sql            # documents / chunks tables
│
├─ src/
│   ├─ backend/
│   │   └─ server.js         # Express API (/health, /ask)
│   │
│   ├─ rag/
│   │   ├─ chunker.js        # Text → chunks (+ overlap)
│   │   ├─ embeddings.js    # OpenAI embeddings
│   │   ├─ retriever.js     # Vector similarity search
│   │   └─ answer.js        # RAG answer generation
│   │
│   ├─ scripts/
│   │   ├─ ingest_web.js    # Web ingestion pipeline
│   │   └─ test_db_minimal.js
│   │
│   ├─ db.js                # Postgres helper
│   │
│   └─ frontend/
│       └─ my-app/           # Next.js frontend
│
└─ README.md
```

---

## ⚙️ Prerequisites

- Node.js ≥ 18
- Docker Desktop
- OpenAI API key

---

## 🐳 Database (Postgres + pgvector)

We intentionally run Postgres in **Docker**:

- No local Postgres conflicts
- pgvector guaranteed
- Fully reproducible setup

### Start database

```bash
docker compose up -d
```

Database is exposed on **port 5433** (not 5432).

---

## 🗄️ Database schema

`sql/schema.sql` defines:

- **documents** — one row per source (URL / file)
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

## 🔐 Environment variables

Create `.env` **(never commit this)**:

```env
DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5433/ragdb
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536
CHAT_MODEL=gpt-4.1-mini
PORT=4000
```

`.env` is ignored via `.gitignore`.

---

## ✅ Verify DB connection

```bash
node src/scripts/test_db_minimal.js
```

Expected:

```
Running minimal DB test...
DB OK: { now: ... }
```

---

## 🌐 Web ingestion

Edit URLs in:

```js
src / scripts / ingest_web.js;
```

Example:

```js
export const URLS = ["https://stripe.com/privacy"];
```

Run ingestion:

```bash
node src/scripts/ingest_web.js
```

Verify:

```bash
docker exec -it rag_pg psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM documents;"
docker exec -it rag_pg psql -U postgres -d ragdb -c "SELECT COUNT(*) FROM chunks;"
```

---

## 🧩 Why chunking is required

Chunking is **mandatory** for RAG:

- Vector search works on small semantic units
- LLMs have context limits
- Overlap prevents broken sentences

Current strategy:

- ~1600 characters per chunk
- ~200 character overlap

This applies to **web pages, PDFs, and markdown** alike.

---

## 🚀 Backend API

### Start backend

```bash
npm run dev
```

Server runs on:

```
http://localhost:4000
```

### Health check

```bash
GET /health
```

### Ask endpoint

```bash
POST /ask
Content-Type: application/json

{
  "question": "What is Stripe's privacy policy about data retention?"
}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    { "ref": "#1", "source": "https://stripe.com/privacy", "distance": 0.12 }
  ]
}
```

Answers are **context‑restricted** and include citations.

---

## 🖥️ Frontend (Next.js)

Frontend lives in:

```
src/frontend/my-app
```

### Start frontend

```bash
cd src/frontend/my-app
npm run dev
```

Open:

```
http://localhost:3000
```

The frontend calls the backend `/ask` endpoint.

---

## 🧠 Design philosophy

- Explicit > abstract
- SQL > black‑box vector DBs
- Inspectable embeddings
- Minimal dependencies

This is a **foundation**, not a SaaS product.

---

## 🔜 Next steps

- Ingest all policy URLs
- Add markdown & PDF ingestion
- Improve section‑aware chunking
- Add conversation memory
- Add auth / roles

---

## 📜 License

MIT
