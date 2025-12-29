# AI-Nutrition-Agent (Telegram Nutrition Bot)

A Telegram bot that tracks your nutrition with AI-powered food recognition and a personal food database.

## Features

- 🧠 **AI-powered parsing** - understands "200g kip" or "magere kwark van AH"
- 💾 **Personal food database** - caches foods in PostgreSQL, learns your items
- 📊 **Google Sheets logging** - daily tracking with macro summaries
- ✓ **Verified foods** - correct AI estimates once, accurate forever
- 🇳🇱 **Dutch-friendly** - recognizes AH, Jumbo, and Dutch products
- 📈 **Smart suggestions** - recommends foods based on remaining macros
- 🎯 **Configurable targets** - set your own daily calorie/macro goals

## How It Works

```
You: "250g magere kwark AH"
         ↓
Bot checks PostgreSQL database
         ↓
Found? → Confirm & log (cached values)
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
├── analytics_service.py  # Remaining macros & suggestions
├── db_models.py          # PostgreSQL models (SQLAlchemy)
├── init_db.py            # Database initialization
├── targets.json          # Saved daily targets (auto-generated)
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

## 5. Google Sheets Setup

1. Create a Google Cloud project
2. Enable Google Sheets API & Google Drive API
3. Create a Service Account and download the JSON key
4. Create a Google Sheet named `Calories_log` with a worksheet `Calories`
5. Share the sheet with your service account email

Sheet columns (no header row needed):
`Date | Item | Quantity | Calories | Fat | Carbs | Protein`

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
2024-12-29 09:00:00 - INFO - 🚀 NutritionBot starting...
```

---

## Telegram Commands

| Command                               | Description                                                |
| ------------------------------------- | ---------------------------------------------------------- |
| `/start`                              | Welcome message                                            |
| `/help`                               | Show all commands and how the bot works                    |
| `/summary`                            | Today's calories & macros vs targets                       |
| `/remaining`                          | What's left to hit your daily targets (with progress bars) |
| `/suggest`                            | Get food suggestions based on what you still need          |
| `/targets`                            | View current daily targets                                 |
| `/targets <cal> <prot> <fat> <carbs>` | Update daily targets                                       |
| `/reset_day`                          | Clear today's entries from Google Sheets                   |

### Example: `/remaining`

```
📊 Remaining for Today

✅ Calories: 0 kcal left
   ██████████ 100%

🔴 Protein: 80g left
   ██████░░░░ 60%

🟢 Fat: 10g left
   ████████░░ 83%

🟡 Carbs: 50g left
   ███████░░░ 70%

💪 Focus on protein to hit your target
```

### Example: `/suggest`

```
💡 Suggested Foods
Based on: 80g protein, 500 kcal remaining

1. Magere Kwark (Albert Heijn) ✓
   📏 250g → 150 kcal, 25g P
   high protein

2. Chicken Breast 🧠
   📏 200g → 220 kcal, 46g P
   high protein

3. Eggs
   📏 2 piece → 140 kcal, 12g P
   frequently used
```

### Example: `/targets`

```
🎯 Daily Targets

• Calories: 2130 kcal
• Protein: 160g
• Fat: 60g
• Carbs: 240g

To update, use:
/targets <cal> <protein> <fat> <carbs>
```

---

## Logging Food

Just send natural text:

```
200g chicken breast
magere kwark AH
2 eggs
1 banana
```

### When Food is Found in Database

```
📦 Found in database ✓

Magere Kwark (Albert Heijn)
📏 250 g

• Calories: 150 kcal
• Protein: 25.0g
• Fat: 0.5g
• Carbs: 7.0g

Use this data?

[✅ Yes, log it] [📝 Update values]
[🆕 Save as new]  [❌ Cancel]
```

Options:

- **Yes, log it** - Use cached values
- **Update values** - Enter new nutrition values, updates existing entry
- **Save as new** - Save as a different food entry
- **Cancel** - Don't log

### When Food is NOT in Database

```
🧠 AI Estimation

Banana
📏 1 piece

• Calories: 89 kcal
• Protein: 1.1g
• Fat: 0.3g
• Carbs: 23g

[✅ Save & Log] [📝 Edit values]
[📋 Log once]   [❌ Cancel]
```

### Editing Values

When you click "Edit values", you choose the input type:

```
📝 How will you enter the values?

[📏 Per 100g]  [🍌 Per piece]
[🍽️ Per serving] [❌ Cancel]
```

Then enter 4 numbers: `calories protein fat carbs`

Example for a banana (per piece): `89 1.1 0.3 23`

---

## Response Indicators

| Symbol | Meaning                              |
| ------ | ------------------------------------ |
| ✅     | Successfully logged                  |
| ✓      | Verified by you (manually corrected) |
| 🧠     | AI estimated (not yet verified)      |
| 📦     | Found in database                    |
| 🔍     | Not in database, using AI            |

---

## Database Schema

### food_items

Your personal food database:

| Column           | Type   | Description                      |
| ---------------- | ------ | -------------------------------- |
| id               | int    | Primary key                      |
| name             | string | Food name                        |
| brand            | string | Brand/store (nullable)           |
| display_name     | string | "Magere Kwark (Albert Heijn)"    |
| search_name      | string | Lowercase for matching           |
| search_brand     | string | Lowercase brand for matching     |
| calories_per_100 | float  | Calories per 100g (or per piece) |
| protein_per_100  | float  | Protein per 100g                 |
| fat_per_100      | float  | Fat per 100g                     |
| carbs_per_100    | float  | Carbs per 100g                   |
| default_serving  | float  | Default serving size             |
| serving_unit     | string | "g", "ml", "piece"               |
| verified         | bool   | User confirmed accuracy          |
| times_used       | int    | Usage counter (for suggestions)  |

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

Use the `/targets` command in Telegram, or edit `targets.json`:

```json
{
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
    "aldi": "aldi",
    "plus": "plus",
    "dirk": "dirk",
    # Add more...
}
```

---

## Troubleshooting

### Bot won't start

```
Missing TELEGRAM_BOT_TOKEN_NUTRITION
```

→ Check your `.env` file exists and has the correct variable name

### Database connection error

```
connection refused
```

→ Make sure PostgreSQL is running: `pg_isready -h localhost -p 5432`

### OpenAI error

```
OPENAI_API_KEY_HW is not set
```

→ Check `.env` has `OPENAI_API_KEY_HW=sk-...`

### Google Sheets error

```
Missing Google service account file
```

→ Check `GOOGLE_SERVICE_ACCOUNT_JSON` path in `.env`

### Summary shows wrong totals

→ Make sure your Google Sheet doesn't have a header row, or add one with column names

---

## Future Improvements

- [ ] Fuzzy matching (pg_trgm) - "magere kwark" matches "magere franse kwark"
- [ ] `/foods` command - list database entries from Telegram
- [ ] `/delete` command - remove foods from database
- [ ] Meal patterns - "my usual breakfast"
- [ ] Weekly/monthly analytics
- [ ] Barcode scanning

---

## License

MIT

---

Happy tracking! 🥗
