"""
Flask API backend for Health Dashboard
Wraps the health-analysis-agent.py functionality and exposes it via REST endpoints
"""

import os
import datetime as dt
from collections import defaultdict
from typing import Any, Optional, Dict, List, Tuple
from flask import Flask, jsonify
from flask_cors import CORS

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# ---- Config ----
DEFAULT_TARGETS = {"calories": 2130.0, "protein": 160.0, "fat": 60.0, "carbs": 240.0}

NUTRITION_SHEET_ID = os.getenv("NUTRITION_SHEET_ID")
EXERCISE_SHEET_ID = os.getenv("EXERCISE_SHEET_ID")
NUTRITION_GOOGLE_SA_JSON = os.getenv("NUTRITION_GOOGLE_SA_JSON", "./nutrition_google.json")
FITNESS_GOOGLE_SA_JSON = os.getenv("FITNESS_GOOGLE_SA_JSON", "./fitness_google.json")
NUTRITION_WORKSHEET = os.getenv("NUTRITION_WORKSHEET")
EXERCISE_WORKSHEET = os.getenv("EXERCISE_WORKSHEET")


# ---- Helper Functions (from health-analysis-agent.py) ----

def get_gspread_client(sa_json_path: str):
    """Creates an authenticated Google Sheets client."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sa_json_path, scope)
    return gspread.authorize(creds)


def safe_float(x: Any) -> float:
    """Safely converts any value to float."""
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return 0.0


def parse_date(s: str) -> Optional[dt.date]:
    """Parses date string using multiple formats."""
    s = (s or "").strip()
    if not s:
        return None

    for fmt in (
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S",
    ):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def header_contains(headers: List[str], needles: List[str]) -> bool:
    """Checks if any header contains any of the search terms."""
    hl = [h.strip().lower() for h in headers]
    for n in needles:
        n = n.lower()
        for h in hl:
            if n in h:
                return True
    return False


def pick_key_contains(row: dict, contains_any: List[str]) -> Optional[str]:
    """Finds the first column name containing any of the search terms."""
    for k in row.keys():
        lk = str(k).strip().lower()
        for needle in contains_any:
            if needle.lower() in lk:
                return k
    return None


def choose_worksheet(sh, forced_name: Optional[str], required_any: List[str]) -> Tuple[str, Any]:
    """Selects the appropriate worksheet from a spreadsheet."""
    if forced_name:
        wanted = forced_name.strip().lower()
        for ws in sh.worksheets():
            if ws.title.strip().lower() == wanted:
                return ws.title, ws
        raise RuntimeError(f"Worksheet '{forced_name}' not found.")

    for ws in sh.worksheets():
        headers = ws.row_values(1)
        if headers and header_contains(headers, required_any):
            return ws.title, ws

    ws = sh.sheet1
    return ws.title, ws


def load_sheet_records(gc, sheet_id: str, forced_worksheet: Optional[str], required_any: List[str]):
    """Opens a Google Sheet and loads all rows as dictionaries."""
    sh = gc.open_by_key(sheet_id)
    ws_name, ws = choose_worksheet(sh, forced_worksheet, required_any)
    
    # Get all values and build records manually to handle empty/duplicate headers
    all_values = ws.get_all_values()
    if not all_values:
        return ws_name, []
    
    # First row is headers
    raw_headers = all_values[0]
    
    # Clean headers: give unique names to empty/duplicate columns
    headers = []
    seen = {}
    for i, h in enumerate(raw_headers):
        h = h.strip()
        if not h:
            h = f"_empty_{i}"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        headers.append(h)
    
    # Build records from remaining rows
    records = []
    for row in all_values[1:]:
        record = {}
        for i, val in enumerate(row):
            if i < len(headers):
                record[headers[i]] = val
        records.append(record)
    
    return ws_name, records


def aggregate_nutrition(records) -> Dict[dt.date, Dict[str, float]]:
    """Aggregates nutrition data by date."""
    by_day = defaultdict(lambda: {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0})

    for r in records:
        if not r:
            continue

        date_key = pick_key_contains(r, ["date", "datum"])
        if not date_key:
            continue

        d = parse_date(str(r.get(date_key, "")).strip())
        if d is None:
            continue

        cal_key = pick_key_contains(r, ["calories", "kcal", "calorie"])
        fat_key = pick_key_contains(r, ["fat", "vet"])
        carb_key = pick_key_contains(r, ["carbs", "koolhyd", "carbo"])
        pro_key = pick_key_contains(r, ["protein", "eiwit", "prote"])

        by_day[d]["calories"] += safe_float(r.get(cal_key)) if cal_key else 0.0
        by_day[d]["fat"] += safe_float(r.get(fat_key)) if fat_key else 0.0
        by_day[d]["carbs"] += safe_float(r.get(carb_key)) if carb_key else 0.0
        by_day[d]["protein"] += safe_float(r.get(pro_key)) if pro_key else 0.0

    return by_day


def aggregate_exercise(records):
    """Aggregates exercise data by date."""
    by_day = defaultdict(lambda: {"minutes": 0.0, "sessions": 0, "types": defaultdict(int)})

    for r in records:
        if not r:
            continue

        date_key = pick_key_contains(r, ["date", "datum"])
        if not date_key:
            continue

        d = parse_date(str(r.get(date_key, "")).strip())
        if d is None:
            continue

        minutes_key = pick_key_contains(r, ["duration", "min", "minutes", "duur"])
        type_key = pick_key_contains(r, ["exercise type", "type", "workout", "activ"])

        mins = safe_float(r.get(minutes_key)) if minutes_key else 0.0
        t = str(r.get(type_key) if type_key else "Unknown").strip() or "Unknown"

        by_day[d]["minutes"] += mins
        by_day[d]["sessions"] += 1
        by_day[d]["types"][t] += 1

    return by_day


def get_health_data(days: int = 7):
    """Fetches and processes health data from Google Sheets."""
    if not NUTRITION_SHEET_ID or not EXERCISE_SHEET_ID:
        raise RuntimeError("Missing NUTRITION_SHEET_ID or EXERCISE_SHEET_ID env vars")

    # Create authenticated clients
    nutrition_gc = get_gspread_client(NUTRITION_GOOGLE_SA_JSON)
    fitness_gc = get_gspread_client(FITNESS_GOOGLE_SA_JSON)

    # Load data from sheets
    _, nutrition_records = load_sheet_records(
        nutrition_gc, NUTRITION_SHEET_ID, NUTRITION_WORKSHEET,
        required_any=["calories", "protein"]
    )
    _, exercise_records = load_sheet_records(
        fitness_gc, EXERCISE_SHEET_ID, EXERCISE_WORKSHEET,
        required_any=["exercise type", "duration"]
    )

    # Aggregate by date
    nut_by_day = aggregate_nutrition(nutrition_records)
    ex_by_day = aggregate_exercise(exercise_records)

    # Build response for last N days
    today = dt.date.today()
    result = []

    for i in range(days - 1, -1, -1):  # Oldest to newest
        d = today - dt.timedelta(days=i)
        nut = nut_by_day.get(d, {"calories": 0, "protein": 0, "carbs": 0, "fat": 0})
        ex = ex_by_day.get(d, {"minutes": 0, "sessions": 0, "types": {}})

        # Convert defaultdict types to regular dict
        types_dict = dict(ex.get("types", {}))

        result.append({
            "date": d.isoformat(),
            "nutrition": {
                "calories": round(nut["calories"], 1),
                "protein": round(nut["protein"], 1),
                "carbs": round(nut["carbs"], 1),
                "fat": round(nut["fat"], 1),
            },
            "exercise": {
                "minutes": round(ex["minutes"], 1),
                "sessions": ex["sessions"],
                "types": types_dict,
            }
        })

    return result


# ---- API Routes ----

@app.route("/api/health", methods=["GET"])
def get_health():
    """Returns health data for the last 7 days."""
    try:
        data = get_health_data(days=7)
        return jsonify({
            "success": True,
            "data": data,
            "targets": DEFAULT_TARGETS,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/health/mock", methods=["GET"])
def get_health_mock():
    """Returns mock data for testing the frontend without Google Sheets."""
    import random
    today = dt.date.today()
    data = []
    
    exercise_types = ["Running", "Weights", "Cycling", "Swimming", "Yoga", "HIIT"]
    
    for i in range(6, -1, -1):
        d = today - dt.timedelta(days=i)
        has_exercise = random.random() > 0.3
        
        types = {}
        if has_exercise:
            num_types = random.randint(1, 2)
            for _ in range(num_types):
                t = random.choice(exercise_types)
                types[t] = types.get(t, 0) + 1
        
        data.append({
            "date": d.isoformat(),
            "nutrition": {
                "calories": round(random.uniform(1800, 2400), 1),
                "protein": round(random.uniform(120, 180), 1),
                "carbs": round(random.uniform(180, 280), 1),
                "fat": round(random.uniform(45, 75), 1),
            },
            "exercise": {
                "minutes": round(random.uniform(30, 90), 1) if has_exercise else 0,
                "sessions": len(types) if has_exercise else 0,
                "types": types,
            }
        })
    
    return jsonify({
        "success": True,
        "data": data,
        "targets": DEFAULT_TARGETS,
        "mock": True,
    })


@app.route("/api/health/<int:days>", methods=["GET"])
def get_health_days(days: int):
    """Returns health data for the specified number of days."""
    try:
        days = min(max(days, 1), 90)  # Clamp between 1-90 days
        data = get_health_data(days=days)
        return jsonify({
            "success": True,
            "data": data,
            "targets": DEFAULT_TARGETS,
        })
    except Exception as e:
        import traceback
        print("=" * 50)
        print("ERROR in /api/health/<days>:")
        print(str(e))
        traceback.print_exc()
        print("=" * 50)
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@app.route("/api/targets", methods=["GET"])
def get_targets():
    """Returns the daily macro targets."""
    return jsonify({
        "success": True,
        "targets": DEFAULT_TARGETS,
    })


@app.route("/api/health/today", methods=["GET"])
def get_today():
    """Returns today's health data only."""
    try:
        data = get_health_data(days=1)
        return jsonify({
            "success": True,
            "data": data[0] if data else None,
            "targets": DEFAULT_TARGETS,
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


if __name__ == "__main__":
    print("=" * 50)
    print("Health Dashboard Backend Starting...")
    print("=" * 50)
    print(f"NUTRITION_SHEET_ID: {'✓ Set' if NUTRITION_SHEET_ID else '✗ MISSING'}")
    print(f"EXERCISE_SHEET_ID: {'✓ Set' if EXERCISE_SHEET_ID else '✗ MISSING'}")
    print(f"NUTRITION_GOOGLE_SA_JSON: {NUTRITION_GOOGLE_SA_JSON} - {'✓ Exists' if os.path.exists(NUTRITION_GOOGLE_SA_JSON) else '✗ NOT FOUND'}")
    print(f"FITNESS_GOOGLE_SA_JSON: {FITNESS_GOOGLE_SA_JSON} - {'✓ Exists' if os.path.exists(FITNESS_GOOGLE_SA_JSON) else '✗ NOT FOUND'}")
    print("=" * 50)
    print("Tip: Use /api/health/mock for testing without Google Sheets")
    print("=" * 50)
    app.run(debug=True, port=5000)