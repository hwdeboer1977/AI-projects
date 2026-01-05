import os
import datetime as dt
from collections import defaultdict
from typing import Any, Optional, Dict, List, Tuple

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables from .env file into os.environ
load_dotenv()

# ---- Config ----
# Daily macro targets used to calculate remaining nutrients
DEFAULT_TARGETS = {"calories": 2130.0, "protein": 160.0, "fat": 60.0, "carbs": 240.0}

# Google Sheet IDs (the long string in the sheet URL)
NUTRITION_SHEET_ID = os.getenv("NUTRITION_SHEET_ID")
EXERCISE_SHEET_ID = os.getenv("EXERCISE_SHEET_ID")

# Paths to service account JSON files for Google Sheets API authentication
# Using separate service accounts allows different permissions per sheet
NUTRITION_GOOGLE_SA_JSON = os.getenv("NUTRITION_GOOGLE_SA_JSON", "./nutrition_google.json")
FITNESS_GOOGLE_SA_JSON = os.getenv("FITNESS_GOOGLE_SA_JSON", "./fitness_google.json")

# Optional: force a specific worksheet/tab name instead of auto-detecting
NUTRITION_WORKSHEET = os.getenv("NUTRITION_WORKSHEET")  # e.g. "Calories"
EXERCISE_WORKSHEET = os.getenv("EXERCISE_WORKSHEET")    # e.g. "Fitness_log"


def require_env(name: str, value: Optional[str]) -> str:
    """
    Validates that an environment variable exists and has a value.
    Fails fast with a clear error message if configuration is missing.
    """
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def get_gspread_client(sa_json_path: str):
    """
    Creates an authenticated Google Sheets client using a service account.
    
    The scope list defines what APIs this client can access:
    - spreadsheets.google.com/feeds: legacy Sheets API
    - spreadsheets: modern Sheets API
    - drive.file / drive: needed for accessing shared sheets
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sa_json_path, scope)
    return gspread.authorize(creds)


def safe_float(x: Any) -> float:
    """
    Safely converts any value to float, returning 0.0 on failure.
    Handles European-style commas as decimal separators (e.g., "3,5" -> 3.5).
    """
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return 0.0


def parse_date(s: str) -> Optional[dt.date]:
    """
    Attempts to parse a date string using multiple common formats.
    Returns None if the string is empty or doesn't match any known format.
    
    Supports both ISO format (2026-01-04) and European format (04-01-2026),
    with or without time components.
    """
    s = (s or "").strip()
    if not s:
        return None

    # Try each format until one works
    for fmt in (
        "%Y-%m-%d",           # ISO: 2026-01-04
        "%d-%m-%Y",           # European: 04-01-2026
        "%d/%m/%Y",           # European with slashes
        "%Y/%m/%d",           # ISO with slashes
        "%Y-%m-%d %H:%M:%S",  # ISO with time
        "%d-%m-%Y %H:%M:%S",  # European with time
    ):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    return None


def header_contains(headers: List[str], needles: List[str]) -> bool:
    """
    Checks if any header contains any of the search terms (case-insensitive).
    Used to auto-detect the correct worksheet by looking for expected columns.
    
    Example: headers=["Date", "Calories", "Protein"] with needles=["calories"]
             returns True because "Calories" contains "calories"
    """
    hl = [h.strip().lower() for h in headers]
    for n in needles:
        n = n.lower()
        for h in hl:
            if n in h:
                return True
    return False


def pick_key_contains(row: dict, contains_any: List[str]) -> Optional[str]:
    """
    Finds the first column name in a row that contains any of the search terms.
    Returns the actual key name (preserving original case) for use with row.get().
    
    Example: row has key "Duration (min)", contains_any=["duration"]
             returns "Duration (min)" so you can do row.get("Duration (min)")
    
    This flexible matching handles variations like:
    - "Calories" vs "Calories (kcal)"
    - "Protein" vs "Protein (g)"
    - Dutch column names like "Eiwit" for protein
    """
    for k in row.keys():
        lk = str(k).strip().lower()
        for needle in contains_any:
            if needle.lower() in lk:
                return k
    return None


def choose_worksheet(sh, forced_name: Optional[str], required_any: List[str]) -> Tuple[str, Any]:
    """
    Selects the appropriate worksheet from a spreadsheet.
    
    If forced_name is provided, uses that exact worksheet.
    Otherwise, auto-detects by finding a worksheet whose headers
    contain any of the required_any terms.
    
    Falls back to the first sheet if no match is found.
    """
    # If user specified a worksheet name, find and use it
    if forced_name:
        wanted = forced_name.strip().lower()
        for ws in sh.worksheets():
            if ws.title.strip().lower() == wanted:
                return ws.title, ws
        raise RuntimeError(
            f"Worksheet '{forced_name}' not found. Available: {[ws.title for ws in sh.worksheets()]}"
        )

    # Auto-detect: find first worksheet with matching headers
    for ws in sh.worksheets():
        headers = ws.row_values(1)
        if headers and header_contains(headers, required_any):
            return ws.title, ws

    # Fallback to first sheet
    ws = sh.sheet1
    return ws.title, ws


def load_sheet_records(gc, sheet_id: str, forced_worksheet: Optional[str], required_any: List[str]):
    """
    Opens a Google Sheet and loads all rows as a list of dictionaries.
    Each dict maps column headers to cell values for that row.
    
    Returns tuple of (worksheet_name, records) for logging purposes.
    """
    sh = gc.open_by_key(sheet_id)
    ws_name, ws = choose_worksheet(sh, forced_worksheet, required_any)
    records = ws.get_all_records()  # Returns list of {header: value} dicts
    return ws_name, records


def aggregate_nutrition(records) -> Dict[dt.date, Dict[str, float]]:
    """
    Aggregates nutrition data by date.
    
    Input: list of row dicts with columns like Date, Calories, Protein, etc.
    Output: dict mapping each date to total macros for that day
    
    Handles multiple meals per day by summing values.
    Uses flexible column matching to support English/Dutch headers.
    """
    # defaultdict creates a new macro dict automatically for each new date
    by_day = defaultdict(lambda: {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0})
    skipped_empty_date = 0
    skipped_bad_date = 0

    for r in records:
        if not r:
            continue

        # Find the date column (could be "Date", "Datum", etc.)
        date_key = pick_key_contains(r, ["date", "datum"])
        if not date_key:
            skipped_empty_date += 1
            continue

        d = parse_date(str(r.get(date_key, "")).strip())
        if d is None:
            raw = str(r.get(date_key, "")).strip()
            if raw == "":
                skipped_empty_date += 1
            else:
                skipped_bad_date += 1
            continue

        # Find each macro column using flexible matching
        # Supports both English ("Calories") and Dutch ("Vet", "Eiwit")
        cal_key = pick_key_contains(r, ["calories", "kcal"])
        fat_key = pick_key_contains(r, ["fat", "vet"])
        carb_key = pick_key_contains(r, ["carbs", "koolhyd", "carbo"])
        pro_key = pick_key_contains(r, ["protein", "eiwit", "prote"])

        # Add this row's values to the running total for this date
        by_day[d]["calories"] += safe_float(r.get(cal_key)) if cal_key else 0.0
        by_day[d]["fat"] += safe_float(r.get(fat_key)) if fat_key else 0.0
        by_day[d]["carbs"] += safe_float(r.get(carb_key)) if carb_key else 0.0
        by_day[d]["protein"] += safe_float(r.get(pro_key)) if pro_key else 0.0

    # Log any data quality issues for debugging
    if skipped_empty_date or skipped_bad_date:
        print(f"[nutrition] Skipped rows: empty-date={skipped_empty_date}, bad-date={skipped_bad_date}")

    return by_day


def aggregate_exercise(records):
    """
    Aggregates exercise data by date.
    
    Input: list of row dicts with columns like Date, Exercise Type, Duration, etc.
    Output: dict mapping each date to exercise stats (minutes, session count, type breakdown)
    
    Tracks workout types separately so you can see "Running×2, Weights×1" etc.
    """
    # Each day gets: total minutes, session count, and a sub-dict counting exercise types
    by_day = defaultdict(lambda: {"minutes": 0.0, "sessions": 0, "types": defaultdict(int)})
    skipped_empty_date = 0
    skipped_bad_date = 0

    for r in records:
        if not r:
            continue

        date_key = pick_key_contains(r, ["date", "datum"])
        if not date_key:
            skipped_empty_date += 1
            continue

        d = parse_date(str(r.get(date_key, "")).strip())
        if d is None:
            raw = str(r.get(date_key, "")).strip()
            if raw == "":
                skipped_empty_date += 1
            else:
                skipped_bad_date += 1
            continue

        # Find duration and exercise type columns
        minutes_key = pick_key_contains(r, ["duration", "min", "minutes", "duur"])
        type_key = pick_key_contains(r, ["exercise type", "type", "workout", "activ"])

        mins = safe_float(r.get(minutes_key)) if minutes_key else 0.0
        t = str(r.get(type_key) if type_key else "Unknown").strip() or "Unknown"

        # Accumulate stats for this date
        by_day[d]["minutes"] += mins
        by_day[d]["sessions"] += 1
        by_day[d]["types"][t] += 1  # Count occurrences of each exercise type

    if skipped_empty_date or skipped_bad_date:
        print(f"[exercise] Skipped rows: empty-date={skipped_empty_date}, bad-date={skipped_bad_date}")

    return by_day


def daterange(end: dt.date, days: int):
    """
    Generator that yields dates going backwards from end date.
    
    Example: daterange(Jan 5, 3) yields Jan 5, Jan 4, Jan 3
    
    Used to iterate over "last N days" for summaries.
    """
    for i in range(days):
        yield end - dt.timedelta(days=i)


def summarize_day(day: dt.date, nut_by_day, ex_by_day, targets=DEFAULT_TARGETS) -> str:
    """
    Creates a formatted summary string for a single day.
    Shows nutrition totals, remaining macros vs targets, and exercise stats.
    
    Returns a multi-line string with emoji formatting for Telegram display.
    """
    # Get data for this day, defaulting to zeros if no data exists
    nut = nut_by_day.get(day, {"calories": 0, "protein": 0, "carbs": 0, "fat": 0})
    ex = ex_by_day.get(day, {"minutes": 0, "sessions": 0, "types": {}})

    # Calculate how much is left to hit each macro target
    rem = {k: targets[k] - nut.get(k, 0.0) for k in targets}

    # Format exercise types as "Running×2, Weights×1", sorted by count descending
    ex_types = ex.get("types", {})
    ex_types_str = ", ".join(
        [f"{k}×{v}" for k, v in sorted(ex_types.items(), key=lambda x: -x[1])]
    ) or "—"

    # Build the output message with emoji prefixes
    msg = []
    msg.append(f"📅 {day.isoformat()}")
    msg.append(
        f"🍽️ Nutrition: {nut['calories']:.0f} kcal | "
        f"P {nut['protein']:.1f}g | C {nut['carbs']:.1f}g | F {nut['fat']:.1f}g"
    )
    msg.append(
        f"🎯 Remaining: {rem['calories']:.0f} kcal | "
        f"P {rem['protein']:.1f}g | C {rem['carbs']:.1f}g | F {rem['fat']:.1f}g"
    )
    msg.append(
        f"🏃 Exercise: {ex['minutes']:.0f} min ({ex['sessions']} sess) | Types: {ex_types_str}"
    )
    return "\n".join(msg)


def summarize_window(end: dt.date, nut_by_day, ex_by_day, days: int):
    """
    Calculates aggregate stats for a time window (e.g., last 7 days).
    
    Returns a dict with:
    - Total and average macros
    - Days with logged data (to show consistency)
    - Total and average exercise minutes
    
    Useful for weekly/monthly trend analysis.
    """
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    ex_total_mins = 0.0
    nutrition_logged_days = 0
    exercise_logged_days = 0

    # Sum up all days in the window
    for d in daterange(end, days):
        nut = nut_by_day.get(d)
        if nut:
            nutrition_logged_days += 1
            for k in totals:
                totals[k] += nut.get(k, 0.0)

        ex = ex_by_day.get(d)
        if ex:
            exercise_logged_days += 1
            ex_total_mins += ex.get("minutes", 0.0)

    # Calculate daily averages (max(days, 1) prevents division by zero)
    avg = {k: (totals[k] / max(days, 1)) for k in totals}

    return {
        "days": days,
        "nutrition_logged_days": nutrition_logged_days,
        "exercise_logged_days": exercise_logged_days,
        "totals": totals,
        "avg_per_day": avg,
        "exercise_minutes_total": ex_total_mins,
        "exercise_minutes_avg": ex_total_mins / max(days, 1),
    }


def main():
    """
    Main entry point: loads data from both sheets and prints today's summary
    plus a 7-day overview.
    """
    # Validate required environment variables are set
    nutrition_sheet_id = require_env("NUTRITION_SHEET_ID", NUTRITION_SHEET_ID)
    exercise_sheet_id = require_env("EXERCISE_SHEET_ID", EXERCISE_SHEET_ID)

    # Create separate authenticated clients for each sheet
    # (in case they use different service accounts with different permissions)
    nutrition_gc = get_gspread_client(NUTRITION_GOOGLE_SA_JSON)
    fitness_gc = get_gspread_client(FITNESS_GOOGLE_SA_JSON)

    # Load nutrition data, auto-detecting worksheet by looking for calorie/protein columns
    nut_ws, nutrition_records = load_sheet_records(
        nutrition_gc,
        nutrition_sheet_id,
        NUTRITION_WORKSHEET,
        required_any=["calories", "protein"],
    )

    # Load exercise data, auto-detecting worksheet by looking for exercise/duration columns
    ex_ws, exercise_records = load_sheet_records(
        fitness_gc,
        exercise_sheet_id,
        EXERCISE_WORKSHEET,
        required_any=["exercise type", "duration"],
    )

    print(f"[info] Using nutrition worksheet: {nut_ws} (rows={len(nutrition_records)})")
    print(f"[info] Using exercise worksheet:  {ex_ws} (rows={len(exercise_records)})")

    # Transform raw records into date-indexed aggregates
    nut_by_day = aggregate_nutrition(nutrition_records)
    ex_by_day = aggregate_exercise(exercise_records)

    # Print today's detailed summary
    today = dt.date.today()
    print()
    print(summarize_day(today, nut_by_day, ex_by_day))

    # Print 7-day trend summary
    w7 = summarize_window(today, nut_by_day, ex_by_day, 7)
    print("\n📈 Last 7 days")
    print(f"- Nutrition logged: {w7['nutrition_logged_days']}/{w7['days']} days")
    print(f"- Exercise logged:  {w7['exercise_logged_days']}/{w7['days']} days")
    print(f"- Avg kcal/day:     {w7['avg_per_day']['calories']:.0f}")
    print(f"- Avg protein/day:  {w7['avg_per_day']['protein']:.1f}g")
    print(f"- Exercise avg:     {w7['exercise_minutes_avg']:.0f} min/day (total {w7['exercise_minutes_total']:.0f} min)")


# Standard Python idiom: only run main() if this file is executed directly,
# not when imported as a module
if __name__ == "__main__":
    main()