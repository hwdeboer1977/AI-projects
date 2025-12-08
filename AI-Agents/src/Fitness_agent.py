# === Fitness_agent.py (PTB v20+, same stack as Nutrition bot) ===
import os
import re
import logging
import datetime as dt

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- ENV & LOGGING ----------
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_FITNESS") or os.getenv("TELEGRAM_BOT_TOKEN")
SERVICE_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_FITNESS_JSON")  # full path to your JSON key

if not TELEGRAM_TOKEN:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN_FITNESS (or TELEGRAM_BOT_TOKEN).")
if not SERVICE_JSON or not os.path.exists(SERVICE_JSON):
    raise SystemExit(f"Missing Google service account JSON at:\n{SERVICE_JSON or '(not set)'}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fitness-bot")

# ---------- CONFIG ----------
SPREADSHEET_NAME = "Fitness_log"   # spreadsheet
WORKSHEET_INDEX = 1                # sheet1 (first worksheet)
USER_WEIGHT_KG = float(os.getenv("FITNESS_USER_WEIGHT_KG", "80"))

# Supported exercise → MET by intensity
MET = {
    "swimming":         {"light": 6.0,  "moderate": 8.0,  "intense": 10.0},
    "walking":          {"light": 2.8,  "moderate": 3.5,  "intense": 4.5},
    "fitness (weights)":{"light": 3.5,  "moderate": 4.5,  "intense": 6.0},
    "fitness (cardio)": {"light": 5.5,  "moderate": 7.0,  "intense": 9.0},
}
ALIASES = {
    "weights": "fitness (weights)",
    "weight": "fitness (weights)",
    "weight training": "fitness (weights)",
    "cardio": "fitness (cardio)",
    "walk": "walking",
    "walked": "walking",
}

INTENSITY_MAP = {
    "low": "light",
    "light": "light",
    "moderate": "moderate",
    "medium": "moderate",
    "high": "intense",
    "intense": "intense",
}

# ---------- SHEETS HELPERS ----------
def _ws():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_JSON, scope)
    client = gspread.authorize(creds)
    # sheet1 = get_worksheet(0); using the classic name to match your old code
    return client.open(SPREADSHEET_NAME).sheet1

def log_to_google_sheets(date_iso, exercise_type, intensity, duration_min, calories):
    ws = _ws()
    ws.append_row([date_iso, exercise_type, intensity, duration_min, round(calories)])

def get_daily_summary_text() -> str:
    try:
        ws = _ws()
        rows = ws.get_all_values()
        today = dt.date.today().isoformat()
        total = 0.0
        for row in rows[1:]:
            if len(row) >= 5 and row[0] == today:
                try:
                    total += float(row[4])
                except Exception:
                    pass
        return f"📊 *Today's Summary:*\n🔥 Total calories burned: {round(total)} kcal"
    except Exception as e:
        logger.exception("summary error")
        return f"❌ Could not retrieve summary. Error: {e}"

def reset_today_rows() -> int:
    ws = _ws()
    rows = ws.get_all_values()
    today = dt.date.today().isoformat()
    to_delete = [i for i, row in enumerate(rows, start=1) if row and row[0] == today]
    for idx in reversed(to_delete):
        ws.delete_rows(idx)
    return len(to_delete)

# ---------- PARSER ----------
def parse_workout(text: str):
    """
    Parse strings like:
      'swimming 45 minutes moderate'
      'fitness (weights) 30 min high'
      'walked 20 minutes'
    Returns (exercise, duration_min, intensity) or (None, None, None) if missing.
    """
    s = (text or "").lower().strip()

    # duration
    dur = None
    m = re.search(r"(\d+)\s*(?:min|mins|minute|minutes)?", s)
    if m:
        try:
            dur = int(m.group(1))
        except Exception:
            pass

    # intensity
    inten = None
    for token in s.split():
        if token in INTENSITY_MAP:
            inten = INTENSITY_MAP[token]
            break
    if inten is None:
        # also accept explicit words inside parentheses "high intensity"
        if "intensity" in s:
            for k in ("light", "moderate", "medium", "high", "intense", "low"):
                if k in s:
                    inten = INTENSITY_MAP.get(k)
                    break

    # exercise
    ex = None
    # try canonical keys
    for key in MET.keys():
        if key in s:
            ex = key
            break
    # try aliases
    if ex is None:
        for k, v in ALIASES.items():
            if k in s:
                ex = v
                break

    return ex, dur, inten

def estimate_calories(exercise: str, intensity: str, duration_min: int) -> float:
    met = MET[exercise][intensity]
    return met * USER_WEIGHT_KG * (duration_min / 60)

# ---------- TELEGRAM HANDLERS (v20 async) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to FitCoachBot!\n"
        "Log workouts like:\n"
        "- 'swimming 45 minutes moderate'\n"
        "- 'fitness (cardio) 20 min high'\n"
        "- 'walked 30 minutes light'\n\n"
        "Commands: /summary /reset_day /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️ *How to use FitCoachBot:*\n\n"
        "1️⃣ Activity: `walking`, `swimming`, `fitness (cardio)`, `fitness (weights)`\n"
        "2️⃣ Duration: e.g. `30 minutes`\n"
        "3️⃣ Intensity: `light`, `moderate`, `intense` (also accepts `low/medium/high`)\n\n"
        "Examples:\n"
        "- `swimming 45 minutes`\n"
        "- `fitness (weights) 30 min moderate`\n"
        "- `walked 20 minutes high`\n\n"
        "🧾 Logged to Google Sheets automatically.\n"
        "🧹 `/reset_day` — remove today's entries\n"
        "📊 `/summary` — show today's total calories",
        parse_mode=ParseMode.MARKDOWN
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_daily_summary_text(), parse_mode=ParseMode.MARKDOWN)

async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = reset_today_rows()
        await update.message.reply_text(f"✅ Removed {n} row(s) for today.")
    except Exception as e:
        logger.exception("reset_day error")
        await update.message.reply_text(f"❌ Could not reset today. Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text or ""
        ex, dur, inten = parse_workout(text)

        missing = []
        if not ex:   missing.append("exercise type")
        if not dur:  missing.append("duration (minutes)")
        if not inten:missing.append("intensity (light/moderate/intense)")

        if missing:
            await update.message.reply_text(f"Got it! Still missing: {', '.join(missing)}.")
            return

        cal = estimate_calories(ex, inten, dur)
        log_to_google_sheets(dt.date.today().isoformat(), ex, inten, dur, cal)

        await update.message.reply_text(
            f"✅ Logged: {dur} min {ex} at {inten} intensity.\n"
            f"≈ {round(cal)} kcal burned. Nice work!"
        )
    except Exception as e:
        logger.exception("handle_message error")
        await update.message.reply_text(f"⚠️ Something went wrong. Error: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ Unexpected error. Please try again.")

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
