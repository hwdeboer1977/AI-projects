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
        
        # Check if we're waiting for a new name
        if context.user_data.get("awaiting_new_name"):
            await handle_new_name(update, context, user_input)
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
            # Found in database - ask for confirmation
            await ask_use_cached(update, context, match, parsed)
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


async def ask_use_cached(update, context, match, parsed):
    """Ask user if they want to use cached data or enter new."""
    food = match.food_item
    nutr = match.scaled_nutrition
    
    # Store match for callback
    context.user_data["cached_match"] = {
        "food_id": food.id,
        "display_name": food.display_name,
        "nutrition": nutr,
        "verified": food.verified
    }
    
    badge = "✓" if food.verified else "🧠"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, log it", callback_data="cache_use"),
            InlineKeyboardButton("📝 Update values", callback_data="cache_update")
        ],
        [
            InlineKeyboardButton("🆕 Save as new", callback_data="cache_new"),
            InlineKeyboardButton("❌ Cancel", callback_data="cache_cancel")
        ]
    ]
    
    await update.message.reply_text(
        f"📦 *Found in database* {badge}\n\n"
        f"*{food.display_name}*\n"
        f"📏 {parsed.quantity} {parsed.unit}\n\n"
        f"• Calories: {nutr['calories']:.0f} kcal\n"
        f"• Protein: {nutr['protein']:.1f}g\n"
        f"• Fat: {nutr['fat']:.1f}g\n"
        f"• Carbs: {nutr['carbs']:.1f}g\n\n"
        f"_Use this data?_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def estimate_new_food(update, context, user_input: str, parsed):
    """AI estimation for unknown food."""
    await update.message.reply_text("🔍 Not in database, asking AI...")

    try:
        estimation = ai_estimate_nutrition(user_input, parsed)
        context.user_data["estimation"] = estimation

        # Calculate for requested quantity
        unit = parsed.unit
        if unit in ["piece", "pieces", "stuk", "stuks", "serving", "servings"]:
            factor = parsed.quantity  # 1 piece = 1x the values
        else:
            factor = parsed.quantity / 100.0
        
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
    cached = context.user_data.get("cached_match", {})

    # === CACHED FOOD CALLBACKS ===
    if data == "cache_use":
        # Use cached data and log
        from food_service import increment_usage
        
        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            cached.get("display_name", raw_input),
            f"{parsed.get('quantity', 1)} {parsed.get('unit', 'g')}",
            cached["nutrition"].get("calories", 0),
            cached["nutrition"].get("fat", 0),
            cached["nutrition"].get("carbs", 0),
            cached["nutrition"].get("protein", 0)
        )
        
        if cached.get("food_id"):
            increment_usage(cached["food_id"])
        
        badge = "✓" if cached.get("verified") else "🧠"
        await query.edit_message_text(
            f"✅ *Logged* {badge}\n\n"
            f"*{cached.get('display_name')}*\n"
            f"• Calories: {cached['nutrition'].get('calories', 0):.0f} kcal\n"
            f"• Protein: {cached['nutrition'].get('protein', 0):.1f}g",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data.clear()
    
    elif data == "cache_update":
        # Update existing food with new values - ask for input type first
        context.user_data["update_existing"] = True
        keyboard = [
            [
                InlineKeyboardButton("📏 Per 100g", callback_data="edit_per100"),
                InlineKeyboardButton("🍌 Per piece", callback_data="edit_perpiece")
            ],
            [
                InlineKeyboardButton("🍽️ Per serving", callback_data="edit_perserving"),
                InlineKeyboardButton("❌ Cancel", callback_data="cache_cancel")
            ]
        ]
        await query.edit_message_text(
            "📝 *How will you enter the values?*\n\n"
            "Choose what your numbers represent:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "cache_new":
        # Save as new entry with different name
        await query.edit_message_text(
            "🆕 *Save as new entry*\n\n"
            "Send the new name for this food:\n\n"
            "Example: `Magere kwark AH 500g`",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["awaiting_new_name"] = True
    
    elif data == "cache_cancel":
        await query.edit_message_text("❌ Cancelled")
        context.user_data.clear()

    # === NEW FOOD CALLBACKS ===
    elif data == "save_yes":
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
        keyboard = [
            [
                InlineKeyboardButton("📏 Per 100g", callback_data="edit_per100"),
                InlineKeyboardButton("🍌 Per piece", callback_data="edit_perpiece")
            ],
            [
                InlineKeyboardButton("🍽️ Per serving", callback_data="edit_perserving"),
                InlineKeyboardButton("❌ Cancel", callback_data="save_cancel")
            ]
        ]
        await query.edit_message_text(
            "📝 *How will you enter the values?*\n\n"
            "Choose what your numbers represent:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data in ["edit_per100", "edit_perpiece", "edit_perserving"]:
        context.user_data["edit_mode"] = data.replace("edit_", "")  # "per100", "perpiece", "perserving"
        
        mode_text = {
            "per100": "per 100g/100ml",
            "perpiece": "per 1 piece/item",
            "perserving": "per 1 serving"
        }
        
        await query.edit_message_text(
            f"📝 *Enter values {mode_text[context.user_data['edit_mode']]}*\n\n"
            "Send 4 numbers:\n"
            "`calories protein fat carbs`\n\n"
            "Example: `89 1.1 0.3 23`",
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
        cached = context.user_data.get("cached_match", {})
        update_existing = context.user_data.get("update_existing", False)
        edit_mode = context.user_data.get("edit_mode", "per100")  # Default to per 100g
        
        # Convert input values to per-100 for storage
        # User entered values as: per100, perpiece, or perserving
        if edit_mode == "per100":
            # Already per 100g, store as-is
            cal_per_100, prot_per_100, fat_per_100, carbs_per_100 = cal, prot, fat, carbs
        else:
            # Values are per piece/serving - store as per-100 but also remember serving size
            # For simplicity, we'll store the per-piece values AS the per-100 values
            # and set default_serving to 1 piece
            cal_per_100, prot_per_100, fat_per_100, carbs_per_100 = cal, prot, fat, carbs
            estimation["serving_unit"] = "piece" if edit_mode == "perpiece" else "serving"
            estimation["default_serving"] = 1

        # Calculate nutrition for the actual logged quantity
        unit = parsed.get("unit", "g")
        quantity = parsed.get("quantity", 1)
        
        if unit in ["piece", "pieces", "stuk", "stuks", "serving", "servings"] or edit_mode in ["perpiece", "perserving"]:
            # For pieces/servings: multiply by quantity
            factor = quantity
        else:
            # For grams: scale by quantity/100
            factor = quantity / 100.0
        
        nutr = {
            "calories": round(cal * factor, 1),
            "protein": round(prot * factor, 1),
            "fat": round(fat * factor, 1),
            "carbs": round(carbs * factor, 1),
        }

        if update_existing and cached.get("food_id"):
            # Update existing food in database
            from food_service import update_food_in_database
            food = update_food_in_database(
                cached["food_id"], 
                cal_per_100, prot_per_100, fat_per_100, carbs_per_100,
                verified=True
            )
            display_name = food.display_name if food else cached.get("display_name", "Unknown")
        else:
            # Save as new verified entry
            estimation["calories_per_100"] = cal_per_100
            estimation["protein_per_100"] = prot_per_100
            estimation["fat_per_100"] = fat_per_100
            estimation["carbs_per_100"] = carbs_per_100

            from food_service import ParsedInput
            parsed_obj = ParsedInput(
                quantity=parsed.get("quantity", 1),
                unit=parsed.get("unit", "piece") if edit_mode != "per100" else parsed.get("unit", "g"),
                food_name=parsed.get("food_name", ""),
                brand=parsed.get("brand")
            )
            food = save_food_to_database(estimation, parsed_obj, verified=True)
            display_name = food.display_name

        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            display_name,
            f"{parsed.get('quantity', 1)} {parsed.get('unit', 'piece')}",
            nutr["calories"], nutr["fat"], nutr["carbs"], nutr["protein"]
        )

        context.user_data["awaiting_edit"] = False
        context.user_data["update_existing"] = False
        context.user_data["edit_mode"] = None

        mode_label = {"per100": "per 100g", "perpiece": "per piece", "perserving": "per serving"}.get(edit_mode, "")
        action = "Updated" if update_existing else "Saved"
        
        await update.message.reply_text(
            f"✅ *{action} & Logged* ✓\n\n"
            f"*{display_name}*\n\n"
            f"Stored: {cal:.0f} kcal, {prot:.0f}g P ({mode_label})\n"
            f"Logged: {nutr['calories']:.0f} kcal, {nutr['protein']:.1f}g P\n\n"
            f"_Marked as verified!_",
            parse_mode=ParseMode.MARKDOWN
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid numbers. Try: `89 1.1 0.3 23`", parse_mode=ParseMode.MARKDOWN)


async def handle_new_name(update, context, new_name: str):
    """Handle saving food under a new name."""
    try:
        cached = context.user_data.get("cached_match", {})
        parsed = context.user_data.get("parsed", {})
        
        # Get the nutrition from cached entry (need to fetch from DB)
        from food_service import get_food_by_id, save_food_with_name
        
        original_food = get_food_by_id(cached.get("food_id"))
        if not original_food:
            await update.message.reply_text("❌ Could not find original food entry.")
            context.user_data.clear()
            return
        
        # Save as new entry with the new name
        new_food = save_food_with_name(
            new_name=new_name,
            calories_per_100=original_food.calories_per_100,
            protein_per_100=original_food.protein_per_100,
            fat_per_100=original_food.fat_per_100,
            carbs_per_100=original_food.carbs_per_100,
            brand=parsed.get("brand"),
            verified=original_food.verified
        )
        
        # Calculate nutrition for quantity
        unit = parsed.get("unit", "g")
        quantity = parsed.get("quantity", 100)
        
        if unit in ["piece", "pieces", "stuk", "stuks", "serving", "servings"]:
            factor = quantity
        else:
            factor = quantity / 100.0
        
        nutr = {
            "calories": round(original_food.calories_per_100 * factor, 1),
            "protein": round(original_food.protein_per_100 * factor, 1),
            "fat": round(original_food.fat_per_100 * factor, 1),
            "carbs": round(original_food.carbs_per_100 * factor, 1),
        }
        
        log_food_to_google_sheets(
            datetime.date.today().isoformat(),
            new_food.display_name,
            f"{parsed.get('quantity', 100)} {parsed.get('unit', 'g')}",
            nutr["calories"], nutr["fat"], nutr["carbs"], nutr["protein"]
        )
        
        context.user_data["awaiting_new_name"] = False
        
        await update.message.reply_text(
            f"✅ *Saved as new & Logged*\n\n"
            f"*{new_food.display_name}*\n\n"
            f"• Calories: {nutr['calories']:.0f} kcal\n"
            f"• Protein: {nutr['protein']:.1f}g\n\n"
            f"_Saved as separate entry!_",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data.clear()
        
    except Exception as e:
        logger.exception("handle_new_name error")
        await update.message.reply_text(f"❌ Error: {e}")


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
