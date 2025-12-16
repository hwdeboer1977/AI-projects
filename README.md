# AI Projects Monorepo

This repository contains multiple AI-related applications combined into a single monorepo.  
Each project keeps its own folder, dependencies, and structure. Some projects run natively on Windows, others inside WSL (Ubuntu).

This monorepo supports:

- A unified workspace
- Shared tooling
- Centralized version control
- Easy expansion with new AI automation projects

---

## 📁 Repository Structure

```
AI-Projects/
│
├── AI-Accounting-Agent/
│   A Telegram-based automated accounting agent.
│   Handles OCR, AI-powered invoice parsing, VAT logic, fallbacks,
│   and automatic storage in Google Sheets.
│
├── AI-Agents/
│   A collection of smaller personal AI agents:
│   - Fitness logging bot
│   - Nutrition assistant
│   - Automation tools
│   Originally developed on Windows.
│
├── Agentic-Newsletter/
│   An autonomous news discovery, clustering, and summarization pipeline.
│   Includes narrative tracking, overlap detection, and thematic analysis.
│   Originally developed in WSL (Ubuntu).
│
└── Web-Summarization-Agent/
    An AI-powered web page summarization engine.
    Fetches a web page, extracts readable content, and generates
    structured summaries using LLMs.
```

---

## 📌 Project Summaries

### **1. AI-Accounting-Agent (Telegram + OCR + LLM)**

A production-ready accounting agent that:

- Accepts invoice photos via Telegram
- Runs OCR with Tesseract
- Extracts invoice fields via OpenAI
- Computes Dutch VAT
- Categorizes expenses
- Handles fallback manual input
- Saves structured data automatically into Google Sheets
- Stores parsed JSON locally for debugging (`src/output/`)

Technologies:  
**OpenAI API, Tesseract.js, node-telegram-bot-api, google-spreadsheet**

---

### **2. AI-Agents (Fitness, Nutrition, Automation)**

A folder containing smaller personal AI agents, such as:

- Fitness tracking bot
- Nutrition agent
- Experimental automation tools

Runs natively on Windows — no WSL required.

---

### **3. Agentic-Newsletter (Autonomous Multi-Agent Pipeline)**

A Linux-native (WSL Ubuntu) autonomous agent system that:

- Fetches news from RSS feeds and APIs
- Performs article clustering and similarity detection
- Summarizes grouped news items
- Generates executive summaries
- Tracks narratives and theme evolution over time

Ideal for:

- Newsletters
- Automated daily briefs
- Narrative and sentiment analysis pipelines

---

### **4. Web-Summarization-Agent (Web Page → Structured Summary)**

An experimental **AI-powered web page summarization agent** that:

- Fetches and renders a single web page
- Extracts readable main content using Mozilla Readability
- Converts HTML to Markdown
- Supports long documents via chunking (map → reduce)
- Generates structured summaries using an LLM

The project explicitly supports **two summarization modes**:

- **Enriched mode** (`summarize_add.js`)  
  Generates learning-oriented, study-note style summaries  
  (may include background knowledge)

- **Strict / Grounded mode** (`summarize_strict.js`)  
  Produces source-faithful summaries only  
  Missing concepts are explicitly marked as:  
  **“Not covered on this page.”**

This project serves as the foundation for:

- a backend summarization API
- a web app (paste URL → summary)
- a browser side-panel extension (summarize current page)

---

## 🛠 Development Guide

### 🔹 Working on Windows-native projects

These include:

- `AI-Accounting-Agent`
- `AI-Agents`
- `Web-Summarization-Agent` (CLI tools)

Open normally in Windows VS Code:

```
Open folder in VS Code → Windows environment
```

All Node.js tooling and scripts run out of the box.

---

### 🔹 Working on WSL-native projects

Applies to:

- `Agentic-Newsletter`

Open via VS Code WSL extension:

```
Open folder in VS Code → Remote WSL (Ubuntu)
```

Or from WSL terminal:

```bash
cd /mnt/c/Users/hwdeb/Documents/blockstat_solutions_github/AI-Projects
code .
```

---

## 🚀 Future Projects

Planned additions to this monorepo include:

- Backend summarization API for web and browser clients
- Browser side-panel summarization extension
- Agentic portfolio optimizer
- Market intelligence and monitoring bots
- Business automation tools
- Additional Telegram-based agents

---

## 👤 Author

**H.W. de Boer**  
AI & Blockchain Engineer  
http
