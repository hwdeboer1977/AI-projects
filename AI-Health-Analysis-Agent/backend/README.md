# Health Dashboard Backend

Flask API backend for the Health Dashboard that aggregates nutrition and exercise data from Google Sheets.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![Flask](https://img.shields.io/badge/Flask-REST_API-000000?logo=flask)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-Integration-34a853?logo=googlesheets)

## Overview

This backend serves as a REST API layer that fetches health data from two Google Sheets (nutrition and exercise), aggregates it by date, and exposes it to the React frontend. It supports flexible date parsing, multi-language column headers (English/Dutch), and includes a mock endpoint for testing without Google Sheets credentials.

## Features

- **Google Sheets Integration** — Reads from separate nutrition and exercise spreadsheets
- **Flexible Column Detection** — Automatically finds columns by partial name match (supports EN/NL)
- **Date Aggregation** — Combines multiple entries per day into daily totals
- **Exercise Type Tracking** — Counts sessions and categorizes by workout type
- **Mock Data Endpoint** — Test the frontend without Google credentials
- **CORS Enabled** — Ready for cross-origin frontend requests

## API Endpoints

| Method | Endpoint             | Description                   |
| ------ | -------------------- | ----------------------------- |
| `GET`  | `/api/health`        | Health data for last 7 days   |
| `GET`  | `/api/health/<days>` | Health data for N days (1-90) |
| `GET`  | `/api/health/today`  | Today's data only             |
| `GET`  | `/api/targets`       | Daily macro/calorie targets   |
| `GET`  | `/api/health/mock`   | Mock data for testing         |

### Response Format

```json
{
  "success": true,
  "data": [
    {
      "date": "2026-01-08",
      "nutrition": {
        "calories": 1850.0,
        "protein": 145.0,
        "carbs": 200.0,
        "fat": 55.0
      },
      "exercise": {
        "minutes": 45.0,
        "sessions": 1,
        "types": { "Weights": 1 }
      }
    }
  ],
  "targets": {
    "calories": 2130.0,
    "protein": 160.0,
    "carbs": 240.0,
    "fat": 60.0
  }
}
```

## Project Structure

```
backend/
├── app.py              # Flask application & API routes
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── nutrition_google.json   # Google SA credentials for nutrition sheet
└── fitness_google.json     # Google SA credentials for exercise sheet
```

## Getting Started

### Prerequisites

- Python 3.10+
- Google Cloud service account with Sheets API access
- Two Google Sheets (nutrition tracking, exercise tracking)

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Google Sheets Setup

1. Create a Google Cloud project and enable the Sheets API
2. Create a service account and download the JSON key file(s)
3. Share your Google Sheets with the service account email
4. Place the JSON key files in the backend directory

### Configuration

Create a `.env` file:

```env
# Google Sheet IDs (from the URL)
NUTRITION_SHEET_ID=your_nutrition_sheet_id_here
EXERCISE_SHEET_ID=your_exercise_sheet_id_here

# Service account JSON paths
NUTRITION_GOOGLE_SA_JSON=./nutrition_google.json
FITNESS_GOOGLE_SA_JSON=./fitness_google.json

# Optional: specific worksheet names
NUTRITION_WORKSHEET=
EXERCISE_WORKSHEET=
```

### Expected Sheet Columns

**Nutrition Sheet** — columns containing (case-insensitive):

- `date` or `datum`
- `calories`, `kcal`, or `calorie`
- `protein`, `eiwit`, or `prote`
- `carbs`, `koolhyd`, or `carbo`
- `fat` or `vet`

**Exercise Sheet** — columns containing:

- `date` or `datum`
- `duration`, `min`, `minutes`, or `duur`
- `exercise type`, `type`, `workout`, or `activ`

### Running the Server

```bash
python app.py
```

Server starts at `http://localhost:5000`

On startup, the console shows configuration status:

```
==================================================
Health Dashboard Backend Starting...
==================================================
NUTRITION_SHEET_ID: ✓ Set
EXERCISE_SHEET_ID: ✓ Set
NUTRITION_GOOGLE_SA_JSON: ./nutrition_google.json - ✓ Exists
FITNESS_GOOGLE_SA_JSON: ./fitness_google.json - ✓ Exists
==================================================
Tip: Use /api/health/mock for testing without Google Sheets
==================================================
```

### Testing Without Google Sheets

Use the mock endpoint to test frontend integration:

```bash
curl http://localhost:5000/api/health/mock
```

Returns randomized but realistic health data for 7 days.

## Dependencies

```
flask
flask-cors
gspread
oauth2client
python-dotenv
```

## Default Targets

The API returns these default daily targets (configurable in `app.py`):

| Macro    | Target    |
| -------- | --------- |
| Calories | 2130 kcal |
| Protein  | 160g      |
| Carbs    | 240g      |
| Fat      | 60g       |

## Related

This backend is part of the **AI-Health-Analysis-Agent** project:

- `frontend/` — React dashboard UI
- `ai_conversational.py` — AI chat interface
- `ai_daily_suggestions.py` — Daily AI recommendations
- `ai_weekly_suggestions.py` — Weekly AI summaries

## License

MIT
