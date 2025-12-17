# AI Projects Monorepo

This repository contains multiple AI-related applications combined into a single monorepo. Each project is self-contained but shares tooling and conventions where possible.

---

## 📁 Repository Structure

```
AI-Projects/
│
├── AI-Accounting-Agent/
├── AI-Agents/
├── Agentic-Newsletter/
├── Web-Summarization-Agent/
├── AI-Knowledge-Agent/
├── AI-Chatbot/
```

---

## 🔹 Project Overview (Short)

### **AI-Accounting-Agent**

Telegram-based accounting automation using OCR + LLMs for invoice parsing, VAT logic, and Google Sheets export.

---

### **AI-Agents**

Collection of smaller personal AI agents (fitness tracking, nutrition, automation experiments).

---

### **Agentic-Newsletter**

Autonomous multi-agent news pipeline for clustering, summarization, and narrative tracking. Linux / WSL focused.

---

### **Web-Summarization-Agent**

Web page → structured summary engine supporting strict (source-grounded) and enriched summarization modes.

---

### **AI-Knowledge-Agent (RAG Internal Q&A)**

A Retrieval-Augmented Generation (RAG) system for internal knowledge and policy documents.

**Core features:**

- Web ingestion (policies, contracts, legal docs)
- Text chunking + OpenAI embeddings
- Vector search using Postgres + pgvector
- `/ask` API endpoint (grounded answers with citations)
- Minimal Next.js frontend
- Dockerized database (safe local persistence)

Designed as a foundation for **internal Q&A assistants**, compliance tools, and company knowledge bases.

---

### **AI-Chatbot**

A customer support chatbot POC for Bolder Outdoor, a fictional e-commerce outdoor gear store.

**Core features:**

- Conversational AI customer support
- Polished outdoor-themed UI
- Full knowledge of products, shipping, returns, and policies
- Quick action buttons for common questions
- Responsive design
- Accessibility support

---

## 🛠 Development Notes

- Some projects run natively on Windows
- Others (Docker / WSL-based) require Linux tooling
- Each project has its own README with setup details

---

## 👤 Author

**H.W. de Boer**  
AI & Blockchain Engineer
