# AI Projects Monorepo

This repository contains multiple AI-related applications combined into a single monorepo. Each project is self-contained but shares tooling and conventions where possible.

---

## 📁 Repository Structure

```
AI-Projects/
│
├── AI-Accounting-Agent/
├── AI-Chatbot/
├── AI-Fitness-Agent/
├── AI-Invoice/
├── AI-Knowledge-Agent/
├── AI-Nutrition-Agent/
├── Agentic-Newsletter/
├── Web-Summarization-Agent/
```

---

## 🔹 Project Overview

### **AI-Accounting-Agent**

Telegram-based accounting automation using OCR + LLMs for invoice parsing, VAT logic, and Google Sheets export.

---

### **AI-Chatbot**

A customer support chatbot POC for Bolder Outdoor, a fictional e-commerce outdoor gear store.

**Core features:**

- Conversational AI customer support
- Polished outdoor-themed UI
- Full knowledge of products, shipping, returns, and policies
- Quick action buttons for common questions

---

### **AI-Fitness-Agent**

Telegram bot for tracking workouts and fitness progress with AI-powered exercise logging.

**Core features:**

- Natural language workout logging ("3x10 bench press 80kg")
- Exercise history tracking
- Progress analytics
- Google Sheets integration

---

### **AI-Invoice**

AI-augmented invoicing system for Dutch ZZP freelancers. Separates deterministic logic (Excel → Word/PDF) from AI enrichment.

**Core features:**

- Professional invoice description rewriting (NL)
- Automated audit/QA (VAT, dates, consistency)
- Smart line item categorization
- Payment reminder generation (escalating tone)

**Design principle:** Excel remains source of truth for all calculations. AI handles text quality, validation, and insights only.

---

### **AI-Knowledge-Agent (RAG Internal Q&A)**

A Retrieval-Augmented Generation (RAG) system for internal knowledge and policy documents.

**Core features:**

- Web ingestion (policies, contracts, legal docs)
- Text chunking + OpenAI embeddings
- Vector search using Postgres + pgvector
- `/ask` API endpoint (grounded answers with citations)

Designed as a foundation for **internal Q&A assistants**, compliance tools, and company knowledge bases.

---

### **AI-Nutrition-Agent**

Telegram bot for tracking daily nutrition with AI-powered food recognition and a personal food database.

**Core features:**

- Natural language food logging ("200g magere kwark AH")
- Personal food database (PostgreSQL) - learns your foods
- AI estimation for unknown foods with manual correction
- Daily macro summaries vs targets
- Google Sheets logging

**Design principle:** Database caches verified foods to reduce API calls and improve accuracy over time.

---

### **Agentic-Newsletter**

Autonomous multi-agent news pipeline for clustering, summarization, and narrative tracking. Linux / WSL focused.

---

### **Web-Summarization-Agent**

Web page → structured summary engine supporting strict (source-grounded) and enriched summarization modes.

---

## 🛠 Development Notes

- Some projects run natively on Windows
- Others (Docker / WSL-based) require Linux tooling
- Each project has its own README with setup details

---

## 👤 Author

**H.W. de Boer**  
AI & Blockchain Engineer
