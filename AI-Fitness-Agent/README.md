# AI-Fitness-Agent (Telegram Fitness / Workout Bot)

A Telegram bot that:

- Parses free‑text workout messages
- Estimates calories burned using MET values
- Logs workouts to Google Sheets
- Provides daily summaries via Telegram commands

This agent uses **the same stable stack** as the Nutrition bot and is confirmed to work on **Windows + PowerShell**.

---

## Prerequisites

- Windows + PowerShell
- Python **3.10+** (Python **3.11 recommended**)
- Telegram Bot Token (via @BotFather)
- Google Cloud project with Service Account JSON
- Google Sheets access

---

## 1. Project structure

```
AI-Fitness-Agent/
├── Fitness_agent.py
├── README.md
├── requirements.txt
├── .env              # NOT committed
└── .venv/            # Local virtual environment
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

## 3. Install dependencies (known‑good versions)

These versions are tested and stable on Windows:

```powershell
pip install python-telegram-bot==21.3 python-dotenv gspread oauth2client
```

Lock versions after install:

```powershell
pip freeze > requirements.txt
```

---

## 4. Environment variables (.env)

Create a `.env` file in the project root:

```env
# Telegram bot token (preferred name)
TELEGRAM_BOT_TOKEN_FITNESS=123456789:AAAbbbCCCdddEEE

# Optional fallback name (also accepted)
# TELEGRAM_BOT_TOKEN=123456789:AAAbbbCCCdddEEE

# Google service account JSON (absolute path recommended)
GOOGLE_SERVICE_ACCOUNT_JSON=C:\Users\hwdeb\secrets\fitnessbot-service-account.json

# User weight (kg) for calorie estimation
FITNESS_USER_WEIGHT_KG=80
```

⚠️ Never commit `.env` or service‑account JSON files.

---

## 5. Supported exercises & intensity

### Exercises

- `walking`
- `swimming`
- `fitness (weights)`
- `fitness (cardio)`

Aliases supported:

- `walk`, `walked`
- `weights`, `weight training`
- `cardio`

### Intensity levels

- `light` / `low`
- `moderate` / `medium`
- `intense` / `high`

---

## 7. Example workout messages

```
swimming 45 minutes moderate
fitness (weights) 30 min high
walked 20 minutes light
```

---

## 8. Telegram commands

- `/start` – welcome message
- `/help` – usage instructions
- `/summary` – today’s total calories burned
- `/reset_day` – delete today’s entries

---

## 9. Run the bot

```powershell
.\.venv\Scripts\Activate.ps1
python Fitness_agent.py
```

If successful, the bot will start polling Telegram.

---

Happy training 💪🤖
