# AI-Nutrition-Agent (Telegram Nutrition Bot)

A Telegram bot that tracks your nutrition with AI-powered food recognition and a personal food database.

## Features

- 🧠 **AI-powered parsing** - understands "200g kip" or "magere kwark van AH"
- 💾 **Personal food database** - caches foods in PostgreSQL, learns your items
- 📊 **Google Sheets logging** - daily tracking with macro summaries
- ✓ **Verified foods** - correct AI estimates once, accurate forever
- 🇳🇱 **Dutch-friendly** - recognizes AH, Jumbo, and Dutch products

## How It Works

```
You: "250g magere kwark AH"
         ↓
Bot checks PostgreSQL database
         ↓
Found? → Log instantly (cached values)
Not found? → AI estimates → You approve/edit → Saved for next time
         ↓
Logged to Google Sheets
```

---

## Project Structure

```
AI-Nutrition-Agent/
├── Nutrition_agent.py    # Main Telegram bot
├── food_service.py       # AI parsing & database lookups
├── db_models.py          # PostgreSQL models (SQLAlchemy)
├── init_db.py            # Database initialization
├── requirements.txt
├── .env                  # Secrets (not committed)
└── .venv/                # Virtual environment
```

---

## Prerequisites

- Windows + PowerShell
- Python **3.10+** (3.11 recommended)
- PostgreSQL **14+** (local install or Docker)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key
- Google Cloud Service Account (for Sheets API)

---

## 1. Clone & Setup Virtual Environment

```powershell
# Clone the repo
git clone <your-repo-url>
cd AI-Nutrition-Agent

# Create virtual environment
python -m venv .venv

# Activate (run every new terminal session)
.\.venv\Scripts\Activate.ps1
```

---

## 2. Install Dependencies

```powershell
pip install python-telegram-bot==21.3 python-dotenv gspread oauth2client openai sqlalchemy psycopg2-binary
```

Or from requirements.txt:

```powershell
pip install -r requirements.txt
```

---

## 3. PostgreSQL Setup

### Option A: Local PostgreSQL (recommended)

If you have PostgreSQL installed locally:

```powershell
# Connect as superuser
psql -U postgres

# Create database and user
CREATE USER nutrition WITH PASSWORD 'nutrition';
CREATE DATABASE nutrition OWNER nutrition;
\q
```

### Option B: Docker

```powershell
docker run -d \
  --name nutrition-db \
  -e POSTGRES_USER=nutrition \
  -e POSTGRES_PASSWORD=nutrition \
  -e POSTGRES_DB=nutrition \
  -p 5433:5432 \
  postgres:16
```

If using Docker on port 5433, update `DATABASE_URL` in `.env`.

---

## 4. Environment Variables

Create `.env` in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN_NUTRITION=123456789:AAAbbbCCCdddEEE

# OpenAI
OPENAI_API_KEY_HW=sk-xxxxxxxxxxxxxxxxxxxx

# PostgreSQL (adjust if using Docker on different port)
DATABASE_URL=postgresql://nutrition:nutrition@localhost:5432/nutrition

# Google Service Account JSON path
GOOGLE_SERVICE_ACCOUNT_JSON=C:\path\to\your-service-account.json
```

⚠️ Never commit `.env` or service account JSON files.

---

## 6. Initialize Database

```powershell
python init_db.py
```

Expected output:

```
✅ Database initialized
```

---

## 7. Run the Bot

```powershell
.\.venv\Scripts\Activate.ps1
python Nutrition_agent.py
```

Expected output:

```
2024-12-27 09:00:00 - INFO - 🚀 NutritionBot starting...
```

---

## Telegram Commands

| Command      | Description                              |
| ------------ | ---------------------------------------- |
| `/start`     | Welcome message                          |
| `/summary`   | Today's calories & macros vs targets     |
| `/reset_day` | Clear today's entries from Google Sheets |
| `/help`      | Show help                                |

### Logging Food

Just send natural text:

```
200g chicken breast
magere kwark AH
2 eggs
1 banana
```

### Response Types

- **✅ Logged from database** - Found in your food cache
- **✓** - Verified by you (you corrected AI values)
- **🧠** - AI estimated (not yet verified)
- **🔍 Not in database** - New food, AI will estimate

### Saving New Foods

When AI estimates a new food, you can:

- **Save & Log** - Add to database for future
- **Edit values** - Correct the macros (per 100g), saves as verified ✓
- **Log once** - Don't save to database
- **Cancel** - Don't log anything

---

## Database Schema

### food_items

Your personal food database:

| Column           | Type   | Description                   |
| ---------------- | ------ | ----------------------------- |
| id               | int    | Primary key                   |
| name             | string | Food name                     |
| brand            | string | Brand/store (nullable)        |
| display_name     | string | "Magere Kwark (Albert Heijn)" |
| search_name      | string | Lowercase for matching        |
| search_brand     | string | Lowercase brand for matching  |
| calories_per_100 | float  | Calories per 100g             |
| protein_per_100  | float  | Protein per 100g              |
| fat_per_100      | float  | Fat per 100g                  |
| carbs_per_100    | float  | Carbs per 100g                |
| verified         | bool   | User confirmed accuracy       |
| times_used       | int    | Usage counter                 |

---

## Viewing Your Database

### pgAdmin (GUI)

1. Open pgAdmin from Start Menu
2. Connect to localhost:5432
3. Navigate: Databases → nutrition → Schemas → public → Tables → food_items
4. Right-click → View/Edit Data → All Rows

### Command Line

```powershell
psql -U nutrition -d nutrition -c "SELECT * FROM food_items;"
```

---

## Configuration

### Daily Targets

Edit in `Nutrition_agent.py`:

```python
DAILY_TARGETS = {
    "calories": 2130.0,
    "protein": 160.0,
    "fat": 60.0,
    "carbs": 240.0
}
```

### Brand Aliases

Edit in `food_service.py`:

```python
BRAND_ALIASES = {
    "ah": "albert heijn",
    "jumbo": "jumbo",
    "lidl": "lidl",
    # Add more...
}
```

---

## Future Improvements

- [ ] Fuzzy matching (pg_trgm) - "magere kwark" matches "magere franse kwark"
- [ ] `/foods` command - list database entries from Telegram
- [ ] Meal patterns - "my usual breakfast"
- [ ] Weekly/monthly analytics
- [ ] Barcode scanning

---

## License

MIT

---

Happy tracking! 🥗
