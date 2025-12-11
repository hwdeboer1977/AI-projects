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
└── Agentic-Newsletter/
    An autonomous news discovery, clustering, and summarization pipeline.
    Includes narrative tracking, overlap detection, and thematic analysis.
    Originally developed in WSL (Ubuntu).
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
**OpenAI Responses API, Tesseract.js, node-telegram-bot-api, google-spreadsheet**

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

- Fetches news (RSS & APIs)
- Performs article clustering / similarity detection
- Summarizes grouped news items
- Generates executive summaries
- Tracks narratives and theme evolution

Ideal for creating newsletters or automated daily briefs.

---

## 🛠 Development Guide

### 🔹 Working on Windows-native projects

These include:

- `AI-Accounting-Agent`
- `AI-Agents`

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

More AI-based tools will be added, such as:

- Agentic portfolio optimizer
- Market intelligence bot
- Business automation tools
- Additional Telegram-based agents

---

## 👤 Author

**H.W. de Boer**  
AI & Blockchain Engineer  
https://blockstatsolutions.com
