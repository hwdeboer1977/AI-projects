# AI-Fitness-Agent (Telegram Fitness / Workout Bot)

A **Telegram-based fitness tracking agent** that logs workouts from natural language messages, estimates calories burned, and stores results in Google Sheets.

The bot is **rules-first and deterministic**, with an **LLM used only as a fallback for language interpretation** when messages are ambiguous or incomplete.

This design keeps the system **cheap, predictable, and auditable**, while still handling messy human input.

---

## ✨ Key Features

- 📝 Parse **free-text workout messages** (English + Dutch)
- 🧠 **LLM fallback** for interpreting ambiguous input (optional)
- 🔢 Deterministic calorie estimation using **MET values**
- 📊 Logs workouts to **Google Sheets**
- 👤 **Multi-user support** (per Telegram user)
- 🔁 Conversational flow (asks follow-up questions when needed)
- ↩️ Undo last entry
- 📅 Daily summaries via Telegram commands

---

## 🧠 AI Design (Important)

This project **does not use AI for calculations or decisions**.

**What the LLM is used for:**

- Interpreting natural language (e.g. “lekker gefietst uurtje stevig”)
- Mapping text → structured fields:
  - exercise
  - duration (minutes)
  - intensity

**What the LLM is NOT used for:**

- Calorie calculations
- Writing to Google Sheets
- Business logic or control flow

> The LLM is only a _language interpreter_, not an executor.

If the LLM is disabled or unavailable, the bot still works using rule-based parsing.

---

## 🏗️ Architecture Overview

```
Telegram message
      ↓
Rule-based parser (regex, keywords)
      ↓ (only if missing/ambiguous)
LLM fallback (JSON-only interpretation)
      ↓
Deterministic logic (MET calories)
      ↓
Google Sheets (persistent storage)
```

---

## 📁 Project Structure

```
AI-Fitness-Agent/
├── Fitness_agent_llm.py   # Main bot (rules + optional LLM fallback)
├── README.md
├── requirements.txt
├── .env                  # NOT committed
└── .venv/                # Local virtual environment
```

---

## ⚙️ Prerequisites

- Windows + PowerShell
- Python **3.10+** (Python **3.11 recommended**)
- Telegram Bot Token (via @BotFather)
- Google Cloud project with Service Account JSON
- Google Sheets access

Optional:

- OpenAI API key (only if LLM fallback is enabled)

---

## 🧪 Environment Setup

### 1. Create & activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

### 2. Install dependencies

```powershell
pip install python-telegram-bot==21.3 python-dotenv gspread oauth2client openai
pip freeze > requirements.txt
```

---

## 🔐 Environment Variables (`.env`)

Create a `.env` file in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN_FITNESS=123456:ABC...

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON=C:\path\to\service-account.json

# Default fallback weight (kg)
FITNESS_USER_WEIGHT_KG=80

# --- Optional LLM fallback ---
OPENAI_API_KEY=sk-...
FITNESS_LLM_ENABLED=1
FITNESS_LLM_MODEL=gpt-4o-mini
```

If `FITNESS_LLM_ENABLED` is not set, the bot runs **rules-only**.

---

## 🏃 Supported Exercises

Canonical types:

- `walking`
- `swimming`
- `fitness (weights)`
- `fitness (cardio)`

Aliases supported (EN + NL):

- `walk`, `wandelen`
- `fietsen`, `cycling`, `bike`
- `weights`, `kracht`, `gym`
- `cardio`

---

## ⚡ Intensity Levels

- `light` / `low` / `laag`
- `moderate` / `medium` / `matig`
- `intense` / `high` / `hoog`

---

## 💬 Example Messages

```
fietsen 45 min matig
swimming 30 minutes intense
lekker gefietst uurtje stevig
fitness weights 40
```

If information is missing, the bot will **ask one follow-up question at a time**.

---

## 🤖 Telegram Commands

- `/start` – welcome message
- `/help` – usage instructions
- `/setweight 78` – set your personal weight (kg)
- `/summary` – today’s totals (per user)
- `/undo` – remove your last logged workout
- `/reset_day` – delete your entries for today

---

## 📊 Google Sheets Schema

Each workout is stored as:

```
date | exercise | intensity | duration_min | calories | user_id | raw_text
```

The `user_id` column enables:

- multi-user summaries
- safe undo
- future analytics (streaks, weekly stats)

You may hide this column in Sheets if desired.

---

## ▶️ Run the Bot

```powershell
.\.venv\Scripts\Activate.ps1
python Fitness_agent_llm.py
```

If successful, the bot will start polling Telegram.

---

## 🧭 Status

- ✅ Production-stable
- ✅ Deterministic core logic
- ✅ Optional AI interpretation
- 🚀 Ready for weekly stats, streaks, or nutrition integration

---

Happy training 💪🤖  
Built with a **rules-first, AI-where-useful** philosophy.
