# === IMPORTS ===
import logging
import os
import datetime
import re

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from food_service import (
    parse_food_input, search_food_database, ai_estimate_nutrition,
    save_food_to_database, increment_usage, scale_nutrition
)

# === ENVIRONMENT SETUP ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_NUTRITION")

# === NUTRITION TARGETS (per day) ===
DAILY_TARGETS = {"calories": 2130.0, "protein": 160.0, "fat": 60.0, "carbs": 240.0}

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nutrition-bot")

# Google Sheets JSON path
SERVICE_JSON_ENV = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
secret_path = SERVICE_JSON_ENV or os.path.join(
    os.path.dirname(__file__), "..", "nutritionbot-472903-72af7ce90bb1.json"
)


# === GOOGLE SHEETS ===
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
    rows = sheet.get_all_values()[1:]

    today = datetime.date.today().isoformat().strip()
    totals = {"calories": 0.0, "fat": 0.0, "carbs": 0.0, "protein": 0.0}

    for row in rows:
        if len(row) >= 7 and row[0].strip() == today:
            totals["calories"] += parse_number(row[3])
            totals["fat"] += parse_number(row[4])
            totals["carbs"] += parse_number(row[5])
            totals["protein"] += parse_number(row[6])

    def pct(val, target):
        return round((val / target) * 100, 1) if target else 0.0

    return (
        f"📊 *Today's Nutrition Summary*\n"
        f"• Calories: {totals['calories']:.0f} kcal ({pct(totals['calories'], DAILY_TARGETS['calories'])}%)\n"
        f"• Protein: {totals['protein']:.0f}g ({pct(totals['protein'], DAILY_TARGETS['protein'])}%)\n"
        f"• Fat: {totals['fat']:.0f}g ({pct(totals['fat'], DAILY_TARGETS['fat'])}%)\n"
        f"• Carbs: {totals['carbs']:.0f}g ({pct(totals['carbs'], DAILY_TARGETS['carbs'])}%)"
    )


# === TELEGRAM HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🥗 *NutritionBot*\n\n"
        "Send me what you ate:\n"
        "• `200g chicken breast`\n"
        "• `magere kwark AH`\n"
        "• `2 eggs`\n\n"
        "I'll check my database first, then use AI if needed.\n\n"
        "/summary - Today's totals\n"
        "/help - More info",
        parse_mode=ParseMode.MARKDOWN
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*How it works:*\n\n"
        "1️⃣ You send a food item\n"
        "2️⃣ I check my database for a match\n"
        "3️⃣ Found → Use cached values (fast!)\n"
        "4️⃣ Not found → AI estimates, you can save it\n\n"
        "✓ = Verified by you\n"
        "🧠 = AI estimated\n\n"
        "/summary - Today's nutrition\n"
        "/reset_day - Clear today",
        parse_mode=ParseMode.MARKDOWN
    )


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = get_daily_summary()
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.exception("summary error")
        await update.message.reply_text(f"❌ Error: {e}")


async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        today = datetime.date.today().isoformat()
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(secret_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Calories_log").worksheet("Calories")
        rows = sheet.get_all_values()
        to_delete = [i for i, row in enumerate(rows, start=1) if row and row[0] == today]
        for idx in reversed(to_delete):
            sheet.delete_rows(idx)
        await update.message.reply_text("✅ Today's log reset!")
    except Exception as e:
        logger.exception("reset_day error")
        await update.message.reply_text(f"❌ Error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler: check DB first, then AI if not found."""
    try:
        user_input = (update.message.text or "").strip()
        if not user_input:
            return

        # Check if we're waiting for manual nutrition input
        if context.user_data.get("awaiting_edit"):
            await handle_manual_edit(update, context, user_input)
            return

        context.user_data["raw_input"] = user_input

        # Parse the input
        parsed = parse_food_input(user_input)
        context.user_data["parsed"] = {
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "food_name": parsed.food_name,
            "brand": parsed.brand
        }

        # Search database
        match = search_food_database(parsed)

        if match:
            # Found in database - log directly
            await log_cached_food(update, context, match, parsed)
        else:
            # Not found - use AI
            await estimate_new_food(update, context, user_input, parsed)

    except Exception as e:
        logger.exception("handle_message error")
        await update.message.reply_text(f"❌ Error: {e}")


async def log_cached_food(update, context, match, parsed):
    """Log food found in database."""
    food = match.food_item
    nutr = match.scaled_nutrition

    log_food_to_google_sheets(
        datetime.date.today().isoformat(),
        food.display_name,
        f"{parsed.quantity} {parsed.unit}",
        nutr["calories"], nutr["fat"], nutr["carbs"], nutr["protein"]
    )

    increment_usage(food.id)

    badge = "✓" if food.verified else "🧠"
    await update.message.reply_text(
        f"✅ *Logged from database* {badge}\n\n"
        f"*{food.display_name}*\n"
        f"📏 {parsed.quantity} {parsed.unit}\n\n"
        f"• Calories: {nutr['calories']:.0f} kcal\n"
        f"• Protein: {nutr['protein']:.1f}g\n"
        f"• Fat: {nutr['fat']:.1f}g\n"
        f"• Carbs: {nutr['carbs']:.1f}g",
        parse_mode=ParseMode.MARKDOWN
    )


async def estimate_new_food(update, context, user_input: str, parsed):
    """AI estimation for unknown food."""
    await update.message.reply_text("🔍 Not in database, asking AI...")

    try:
        estimation = ai_estimate_nutrition(user_input, parsed)
        context.user_data["estimation"] = estimation

        # Calculate for requested quantity
        factor = parsed.quantity / 100.0 if parsed.unit in ["g", "ml"] else 1
        nutr = {
            "calories": round(estimation.get("calories_per_100", 0) * factor, 1),
            "protein": round(estimation.get("protein_per_100", 0) * factor, 1),
            "fat": round(estimation.get("fat_per_100", 0) * factor, 1),
            "carbs": round(estimation.get("carbs_per_100", 0) * factor, 1),
        }
        context.user_data["calculated_nutrition"] = nutr

        brand_text = f" ({estimation.get('brand')})" if estimation.get('brand') else ""

        keyboard = [
            [
                InlineKeyboardButton("✅ Save & Log", callback_data="save_yes"),
                InlineKeyboardButton("📝 Edit values", callback_data="save_edit")
            ],
            [
                InlineKeyboardButton("📋 Log once", callback_data="save_once"),
                InlineKeyboardButton("❌ Cancel", callback_data="save_cancel")
            ]
        ]

        await update.message.reply_text(
            f"🧠 *AI Estimation*\n\n"
            f"*{estimation.get('name', user_input)}*{brand_text}\n"
            f"📏 {parsed.quantity} {parsed.unit}\n\n"
            f"• Calories: {nutr['calories']:.0f} kcal\n"
            f"• Protein: {nutr['protein']:.1f}g\n"
            f"• Fat: {nutr['fat']:.1f}g\n"
            f"• Carbs: {nutr['carbs']:.1f}g\n\n"
            f"_Per 100{estimation.get('serving_unit', 'g')}: "
            f"{estimation.get('calories_per_100', 0):.0f} kcal, "
            f"{estimation.get('protein_per_100', 0):.0f}g protein_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.exception("estimation error")
        await update.message.reply_text(f"❌ AI estimation failed: {e}")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    raw_input = context.user_data.get("raw_input", "")
    parsed = context.user_data.get("parsed", {})
    estimation = context.user_data.get("estimation", {})
    nutr = context.user_data.get("calculated_nutrition", {})

    if data == "save_yes":
        # Save to database and log
        food = save_food_to_database(estimation, type('P', (), parsed)(), verified=False)

        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            food.display_name,
            f"{parsed.get('quantity', 1)} {parsed.get('unit', 'g')}",
            nutr.get("calories", 0), nutr.get("fat", 0),
            nutr.get("carbs", 0), nutr.get("protein", 0)
        )

        await query.edit_message_text(
            f"✅ *Saved & Logged*\n\n"
            f"*{food.display_name}* 🧠\n\n"
            f"• Calories: {nutr.get('calories', 0):.0f} kcal\n"
            f"• Protein: {nutr.get('protein', 0):.1f}g\n\n"
            f"_Saved for next time!_",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "save_once":
        # Log without saving
        name = estimation.get("name", raw_input)
        brand = estimation.get("brand")
        display = f"{name} ({brand})" if brand else name

        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            display,
            f"{parsed.get('quantity', 1)} {parsed.get('unit', 'g')}",
            nutr.get("calories", 0), nutr.get("fat", 0),
            nutr.get("carbs", 0), nutr.get("protein", 0)
        )

        await query.edit_message_text(
            f"✅ *Logged once* (not saved)\n\n"
            f"*{display}*\n"
            f"• Calories: {nutr.get('calories', 0):.0f} kcal",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "save_edit":
        await query.edit_message_text(
            "📝 *Edit per-100g values*\n\n"
            "Send 4 numbers:\n"
            "`calories protein fat carbs`\n\n"
            "Example: `60 10 0.2 4`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["awaiting_edit"] = True

    elif data == "save_cancel":
        await query.edit_message_text("❌ Cancelled")
        context.user_data.clear()


async def handle_manual_edit(update, context, text: str):
    """Handle manually entered nutrition values."""
    try:
        values = text.strip().split()
        if len(values) != 4:
            await update.message.reply_text(
                "❌ Send 4 numbers: `calories protein fat carbs`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        cal, prot, fat, carbs = map(float, values)

        parsed = context.user_data.get("parsed", {})
        estimation = context.user_data.get("estimation", {})

        # Update estimation with corrected values
        estimation["calories_per_100"] = cal
        estimation["protein_per_100"] = prot
        estimation["fat_per_100"] = fat
        estimation["carbs_per_100"] = carbs

        # Save as verified
        from food_service import ParsedInput
        parsed_obj = ParsedInput(
            quantity=parsed.get("quantity", 100),
            unit=parsed.get("unit", "g"),
            food_name=parsed.get("food_name", ""),
            brand=parsed.get("brand")
        )
        food = save_food_to_database(estimation, parsed_obj, verified=True)

        # Calculate for actual quantity
        factor = parsed.get("quantity", 100) / 100.0
        nutr = {
            "calories": round(cal * factor, 1),
            "protein": round(prot * factor, 1),
            "fat": round(fat * factor, 1),
            "carbs": round(carbs * factor, 1),
        }

        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            food.display_name,
            f"{parsed.get('quantity', 100)} {parsed.get('unit', 'g')}",
            nutr["calories"], nutr["fat"], nutr["carbs"], nutr["protein"]
        )

        context.user_data["awaiting_edit"] = False

        await update.message.reply_text(
            f"✅ *Saved & Logged* ✓\n\n"
            f"*{food.display_name}*\n\n"
            f"Per 100g: {cal:.0f} kcal, {prot:.0f}g P\n"
            f"Logged: {nutr['calories']:.0f} kcal, {nutr['protein']:.1f}g P\n\n"
            f"_Marked as verified!_",
            parse_mode=ParseMode.MARKDOWN
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid numbers. Try: `60 10 0.2 4`", parse_mode=ParseMode.MARKDOWN)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ Something went wrong.")


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN_NUTRITION")
    if not os.path.exists(secret_path):
        raise SystemExit(f"Missing Google service account file: {secret_path}")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("🚀 NutritionBot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
