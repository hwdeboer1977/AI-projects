# AI Health Analysis Agent (Google Sheets)

> ⚠️ **Work in Progress** — This project is under active development.

This project contains a **local Python analysis agent** that reads nutrition and exercise data from two Google Sheets, aggregates them, and provides **AI-powered insights** — plus a **React dashboard** and **Flask API** for visual tracking.

## Data Sources

This agent pulls data from two separate bots:

- **[AI Nutrition Agent](https://github.com/hwdeboer1977/AI-projects/tree/main/AI-Nutrition-Agent)** — logs food items with calories and macros
- **[AI Fitness Agent](https://github.com/hwdeboer1977/AI-projects/tree/main/AI-Fitness-Agent)** — logs exercise sessions with duration and type

The Health Analysis Agent acts as the **analytical layer** on top of these bots, combining both data sources for unified insights.

---

## Features

### Core Analysis (`health-analysis-agent.py`)

Deterministic aggregation of your logs:

- **Daily summary** — calories, macros, remaining targets, exercise stats
- **7-day summary** — averages, totals, logged days

### AI Modules

| Module                     | File                       | Description                                                                                                    |
| -------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Daily Suggestions**      | `ai_daily_suggestions.py`  | Analyzes today's remaining macros and suggests specific foods to hit your targets                              |
| **Weekly Coach**           | `ai_weekly_suggestions.py` | Reviews a full week of data and provides 3 personalized insights about patterns, progress, and actionable tips |
| **Conversational Queries** | `ai_conversational.py`     | Ask natural language questions like "How was my protein this week?" or "Did I exercise yesterday?"             |

### Web Dashboard

| Component    | Directory   | Description                                                          |
| ------------ | ----------- | -------------------------------------------------------------------- |
| **Frontend** | `frontend/` | React dashboard with charts, macro tracking, and 7-day trends        |
| **Backend**  | `backend/`  | Flask REST API that serves aggregated health data from Google Sheets |

---

## What the script does

### Nutrition (Calories sheet)

The nutrition sheet is item-based:

| Date | Item | Quantity | Calories | Fat | Carbs | Protein |
| ---- | ---- | -------- | -------- | --- | ----- | ------- |

Each row represents **one food item**. The script:

- Groups rows by `Date`
- **Sums calories, protein, carbs, and fat per day**

---

### Exercise (Fitness_log sheet)

The exercise sheet is session-based:

| Date | Exercise Type | Intensity | Duration (min) | Calories Burned | User ID | Raw Input |
| ---- | ------------- | --------- | -------------- | --------------- | ------- | --------- |

Each row represents **one exercise session**. The script:

- Groups rows by `Date`
- Sums total minutes per day
- Counts sessions per day
- Tracks exercise types per day

---

## Folder structure

```
AI-Health-Analysis-Agent/
├── health-analysis-agent.py    # Core aggregation logic
├── ai_daily_suggestions.py     # AI: daily food suggestions
├── ai_weekly_suggestions.py    # AI: weekly pattern analysis
├── ai_conversational.py        # AI: natural language queries
├── backend/                    # Flask REST API
│   ├── app.py                  # API routes & Google Sheets integration
│   ├── requirements.txt
│   └── .env
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── HealthDashboard.jsx
│   │   │   └── HealthDashboard.css
│   │   ├── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── .env
├── nutrition_google.json
├── fitness_google.json
├── requirements.txt
└── README.md
```

⚠️ **Do not commit service account JSON files or `.env` to Git.**

---

## Requirements

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install gspread oauth2client python-dotenv openai
```

Freeze dependencies:

```powershell
pip freeze > requirements.txt
```

---

## Environment variables

Create a `.env` file in the project root:

```env
# Google Sheet IDs (from the URL)
NUTRITION_SHEET_ID=your-nutrition-sheet-id
EXERCISE_SHEET_ID=your-exercise-sheet-id

# Separate service accounts
NUTRITION_GOOGLE_SA_JSON=./nutrition_google.json
FITNESS_GOOGLE_SA_JSON=./fitness_google.json

# Explicit worksheet/tab names (recommended)
NUTRITION_WORKSHEET=Calories
EXERCISE_WORKSHEET=Fitness_log

# OpenAI API key (required for AI modules)
OPENAI_API_KEY=sk-proj-your-key-here
```

---

## Service account access

This project uses **two different Google service accounts**:

- One for the **nutrition sheet**
- One for the **fitness sheet**

### Share each Google Sheet with the correct service account email

1. Open the Google Sheet in your browser
2. Click **Share**
3. Add the service account email as **Viewer** or **Editor**

### Check service account emails

```powershell
python -c "import json; print(json.load(open('nutrition_google.json'))['client_email'])"
python -c "import json; print(json.load(open('fitness_google.json'))['client_email'])"
```

---

## Running the scripts

### Core analysis

```powershell
python health-analysis-agent.py
```

Example output:

```
[info] Using nutrition worksheet: Calories (rows=33)
[info] Using exercise worksheet:  Fitness_log (rows=9)

📅 2026-01-03
🍽️ Nutrition: 1763 kcal | P 145.1g | C 200.2g | F 67.4g
🎯 Remaining: 367 kcal | P 14.9g | C 39.8g | F -7.4g
🏃 Exercise: 60 min (3 sess) | Types: walking×2, fitness (weights)×1

📈 Last 7 days
- Nutrition logged: 3/7 days
- Exercise logged:  3/7 days
- Avg kcal/day:     821
- Avg protein/day:  52.3g
- Exercise avg:     20 min/day (total 140 min)
```

### AI modules (standalone testing)

```powershell
# Daily suggestion based on sample data
python ai_daily_suggestions.py

# Weekly coaching insights
python ai_weekly_suggestions.py

# Interactive chat (ask questions about your data)
python ai_conversational.py
```

---

## Web Dashboard

The web dashboard provides a visual interface for tracking your health data.

### Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env`:

```env
NUTRITION_SHEET_ID=your-nutrition-sheet-id
EXERCISE_SHEET_ID=your-exercise-sheet-id
NUTRITION_GOOGLE_SA_JSON=./nutrition_google.json
FITNESS_GOOGLE_SA_JSON=./fitness_google.json
```

Start the API server:

```powershell
python app.py
```

Server runs at `http://localhost:5000`

#### API Endpoints

| Method | Endpoint             | Description                   |
| ------ | -------------------- | ----------------------------- |
| `GET`  | `/api/health`        | Health data for last 7 days   |
| `GET`  | `/api/health/<days>` | Health data for N days (1-90) |
| `GET`  | `/api/health/today`  | Today's data only             |
| `GET`  | `/api/targets`       | Daily macro/calorie targets   |
| `GET`  | `/api/health/mock`   | Mock data for testing         |

### Frontend Setup

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:5000
```

Start the dev server:

```powershell
npm run dev
```

Dashboard runs at `http://localhost:5173`

### Dashboard Features

- **Calorie Ring** — circular progress with remaining/over indicator
- **Macro Bars** — protein, carbs, fat progress against targets
- **Exercise Card** — daily minutes, sessions, workout types
- **7-Day Charts** — calorie trend (line) and exercise minutes (bar)
- **Weekly Summary** — averages and logging streaks
- **Day Selector** — navigate between the last 7 days

### Running Both Together

Terminal 1 (backend):

```powershell
cd backend && python app.py
```

Terminal 2 (frontend):

```powershell
cd frontend && npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Common errors & fixes

| Error                                      | Cause                                 | Fix                                         |
| ------------------------------------------ | ------------------------------------- | ------------------------------------------- |
| `403: The caller does not have permission` | Sheet not shared with service account | Share sheet with `client_email` from JSON   |
| `WorksheetNotFound`                        | Worksheet name mismatch               | Use exact tab name from Google Sheets       |
| `OpenAIError: api_key must be set`         | Missing API key                       | Add `OPENAI_API_KEY` to `.env`              |
| Empty dates or zero totals                 | No logs for that day                  | Expected behavior, script skips empty dates |
| `CORS error` in browser                    | Backend not running or wrong URL      | Ensure backend is running on port 5000      |
| `Failed to fetch` in frontend              | API connection issue                  | Check `VITE_API_URL` in frontend `.env`     |

---

## Next steps

Planned extensions:

- [x] Web dashboard with React frontend
- [x] REST API backend
- [ ] Integrate AI modules into main script
- [ ] CLI flags: `--date`, `--week`, `--month`
- [ ] Telegram commands: `/today`, `/week`, `/coach`
- [ ] Natural language food logging ("had 2 eggs for breakfast")
- [ ] Deployment as background worker (Render/VPS)
- [ ] Dashboard authentication
- [ ] Historical data export (CSV/PDF)

---

## Security notes

Add the following to `.gitignore`:

```
.env
*.json
.venv/
node_modules/
dist/
```

Never commit credentials to version control.

---

## License

MIT
