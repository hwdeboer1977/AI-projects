# === IMPORTS ===
import logging
import os
import datetime
import json
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI

# === ENVIRONMENT SETUP ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_NUTRITION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_HW")
IS_LOCAL = True  # or read from env

# === NUTRITION TARGETS (per day) ===
DAILY_TARGETS = {"calories": 2130.0, "protein": 160.0, "fat": 60.0, "carbs": 240.0}

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nutrition-bot")

# === EXTRA LOG FILE (optional) ===
logging.basicConfig(
    level=logging.INFO,
    filename="nutrition_bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Location for Google Sheets JSON
SERVICE_JSON_ENV = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
secret_path = SERVICE_JSON_ENV or os.path.join(
    os.path.dirname(__file__), "..", "nutritionbot-472903-72af7ce90bb1.json"
)

# === GOOGLE SHEETS LOGGING FUNCTION ===
def log_food_to_google_sheets(date, item, quantity, calories, fat, carbs, protein):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(secret_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Calories_log").worksheet("Calories")
    sheet.append_row([date, item, quantity, calories, fat, carbs, protein])

def get_daily_summary():
    def parse_number(cell):
        try:
            return float(re.sub(r"[^\d.]", "", str(cell).strip()))
        except:
            return 0.0

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(secret_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Calories_log").worksheet("Calories")
    rows = sheet.get_all_values()[1:]  # Skip header

    today = datetime.date.today().isoformat().strip()
    totals = {"calories": 0.0, "fat": 0.0, "carbs": 0.0, "protein": 0.0}

    for row in rows:
        if len(row) >= 7 and row[0].strip() == today:
            totals["calories"] += parse_number(row[3])
            totals["fat"]      += parse_number(row[4])
            totals["carbs"]    += parse_number(row[5])
            totals["protein"]  += parse_number(row[6])

    def percent(val, target):
        return round((val / target) * 100, 1) if target else 0.0

    pct = {
        "calories": percent(totals["calories"], DAILY_TARGETS["calories"]),
        "protein":  percent(totals["protein"],  DAILY_TARGETS["protein"]),
        "fat":      percent(totals["fat"],      DAILY_TARGETS["fat"]),
        "carbs":    percent(totals["carbs"],    DAILY_TARGETS["carbs"])
    }

    return (f"📊 *Today's Nutrition Summary*\n"
            f"- Calories: {totals['calories']} kcal ({pct['calories']}%)\n"
            f"- Protein: {totals['protein']}g ({pct['protein']}%)\n"
            f"- Fat: {totals['fat']}g ({pct['fat']}%)\n"
            f"- Carbs: {totals['carbs']}g ({pct['carbs']}%)")

# === JSON UTILITIES ===
def extract_json_safe(text):
    try:
        # Allow code fences, take the last JSON object
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
        matches = list(re.finditer(r"\{.*?\}", text, flags=re.DOTALL))
        if not matches:
            raise ValueError("No JSON object found")
        return json.loads(matches[-1].group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")

def clean_numeric(val):
    if isinstance(val, str):
        return float(re.sub(r"[^\d.]", "", val) or 0)
    return float(val or 0)

# === OpenAI helper ===
def ai_parse_food(food_input: str) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY_HW is not set")
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = (
        "You are a strict JSON API. Respond ONLY with JSON in this schema:\n"
        '{ "item": string, "quantity": string, "calories": number, "fat": number, "carbs": number, "protein": number }\n'
        f"Input: {food_input}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a nutritionist that only returns strict JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    entry = extract_json_safe(resp.choices[0].message.content.strip())
    entry["calories"] = clean_numeric(entry["calories"])
    for k in ("fat", "carbs", "protein"):
        entry[k] = clean_numeric(entry[k])
    return entry

# === TELEGRAM HANDLERS (v20+ need async) ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥗 Welcome to NutritionBot! Send me what you ate, like '1 banana' or '200g chicken'.\n"
        "Commands: /summary /reset_day /help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Here are the available commands:\n\n"
        "/start - Welcome message\n"
        "/summary - Today's nutrition summary\n"
        "/reset_day - Reset today's logged data\n"
        "/help - This help\n\n"
        "You can also just type meals (e.g., '1 apple', '200g chicken')."
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = get_daily_summary()
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.exception("summary error")
        await update.message.reply_text(f"❌ Could not get summary. Error: {e}")

async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        today = datetime.date.today().isoformat()
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(secret_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Calories_log").worksheet("Calories")
        rows = sheet.get_all_values()
        to_delete = [i for i, row in enumerate(rows, start=1) if row and row[0] == today]
        for idx in reversed(to_delete):
            sheet.delete_rows(idx)
        await update.message.reply_text("✅ Today's log has been reset. You can start logging again!")
    except Exception as e:
        logger.exception("reset_day error")
        await update.message.reply_text(f"❌ Could not reset the day. Error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = (update.message.text or "").strip()
        if not user_input:
            return
        entry = ai_parse_food(user_input)

        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            entry["item"], entry["quantity"],
            entry["calories"], entry["fat"], entry["carbs"], entry["protein"]
        )

        msg = (
            f"✅ Logged: {entry['quantity']} {entry['item']}\n"
            f"Calories: {entry['calories']} kcal\n"
            f"Fat: {entry['fat']}g, Carbs: {entry['carbs']}g, Protein: {entry['protein']}g"
        )
        await update.message.reply_text(msg)

    except Exception as e:
        logger.exception("handle_message error")
        await update.message.reply_text(f"❌ Could not log nutrition data. Error: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception in handler", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ Something went wrong. Please try again.")

def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN_NUTRITION")
    if not os.path.exists(secret_path):
        raise SystemExit(f"Missing Google service account file at {secret_path}")

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
