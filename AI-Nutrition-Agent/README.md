# AI-Nutrition-Agent (Telegram Nutrition Bot)

A Telegram bot that:

- Parses food entries using OpenAI (strict JSON)
- Logs calories & macros to Google Sheets
- Provides daily summaries via Telegram commands

This README documents the **exact working setup on Windows**, including pinned package versions.

---

## Prerequisites

- Windows + PowerShell
- Python **3.10+** (Python **3.11 recommended**)
- Telegram Bot Token (from @BotFather)
- OpenAI API Key
- Google Sheets + Google Cloud Service Account (JSON key)

---

## 1. Project setup

Clone or open the project folder:

```
AI-Nutrition-Agent/
├── Nutrition_agent.py
├── README.md
├── requirements.txt
├── .env              # NOT committed
└── .venv/            # Virtual environment (local)
```

---

## 2. Create & activate virtual environment

Run **once per project**:

```powershell
python -m venv .venv
```

Activate **every time you open a new terminal**:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```
(.venv)
```

---

## 3. Install dependencies (known-good versions)

These versions are confirmed to work on Windows:

```powershell
pip install python-telegram-bot==21.3 python-dotenv gspread oauth2client openai
```

Lock dependencies:

```powershell
pip freeze > requirements.txt
```

---

## 4. Environment variables (.env)

Create a file called `.env` in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN_NUTRITION=123456789:AAAbbbCCCdddEEE

# OpenAI
OPENAI_API_KEY_HW=sk-xxxxxxxxxxxxxxxxxxxx

# Google Service Account JSON (absolute path recommended)
GOOGLE_SERVICE_ACCOUNT_JSON=C:\Users\hwdeb\secrets\nutritionbot-service-account.json
```

⚠️ Never commit `.env` or service-account JSON files.

---

## 6. Run the bot

```powershell
.\.venv\Scripts\Activate.ps1
python Nutrition_agent.py
```

If successful, the bot will start polling Telegram.

---

## 7. Telegram commands

- `/start` – welcome message
- `/summary` – today’s macro totals
- `/reset_day` – remove today’s entries
- Send food directly, e.g.:
  - `250g magere kwark`
  - `1 banana`

---

Happy building �
