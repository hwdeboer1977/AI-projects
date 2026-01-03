# === Fitness_agent.py (PTB v20+, improved UX + multi-user) ===
import os
import re
import logging
import datetime as dt
import json
from typing import Optional, Tuple, Dict, Any

from dotenv import load_dotenv

# Optional: LLM for interpretation only
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except Exception:
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
SERVICE_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")  # full path to your JSON key

if not TELEGRAM_TOKEN:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN_FITNESS (or TELEGRAM_BOT_TOKEN).")
if not SERVICE_JSON or not os.path.exists(SERVICE_JSON):
    raise SystemExit(f"Missing Google service account JSON at:\n{SERVICE_JSON or '(not set)'}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fitness-bot")

# ---------- CONFIG ----------
SPREADSHEET_NAME = "Fitness_log"
WORKSHEET_INDEX = int(os.getenv("FITNESS_WORKSHEET_INDEX", "0"))  # 0-based. default: first sheet
DEFAULT_WEIGHT_KG = float(os.getenv("FITNESS_USER_WEIGHT_KG", "80"))

# --- LLM (interpretation only) ---
# Set OPENAI_API_KEY in your environment to enable.
LLM_ENABLED = (
    os.getenv("FITNESS_LLM_ENABLED", "1") == "1"
    and _OPENAI_AVAILABLE
    and bool(os.getenv("OPENAI_API_KEY_HW"))
)
LLM_MODEL = os.getenv("FITNESS_LLM_MODEL", "gpt-4o-mini")

_llm_client = None

def _get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI()  # uses OPENAI_API_KEY env var
    return _llm_client

# Strict schema for structured output
WORKOUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "exercise": {"type": ["string", "null"], "enum": [
            None,
            "swimming",
            "walking",
            "fitness (weights)",
            "fitness (cardio)",
            "cycling",
        ]},
        "duration_min": {"type": ["integer", "null"], "minimum": 1, "maximum": 600},
        "intensity": {"type": ["string", "null"], "enum": [None, "light", "moderate", "intense"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "notes": {"type": ["string", "null"]},
    },
    "required": ["exercise", "duration_min", "intensity", "confidence", "notes"],
}

async def llm_interpret_workout(user_text: str, pending: Dict[str, Any]) -> Dict[str, Any]:
    """Use an LLM to interpret messy user input into structured fields.

    This function ONLY extracts fields; it does not decide calories, logging, or business logic.
    """
    if not LLM_ENABLED:
        return {}

    # Provide current partial state so the model can fill gaps.
    partial = {
        "exercise": pending.get("exercise"),
        "duration_min": pending.get("duration_min"),
        "intensity": pending.get("intensity"),
    }

    system = (
        "You are a workout text parser. Extract exercise, duration in minutes, and intensity from a short message. "
        "Support Dutch and English. Map synonyms: fietsen/bike/cycling->cycling; wandelen/walk->walking; zwemmen/swim->swimming; "
        "kracht/weights/gym->fitness (weights); cardio/rennen/hardlopen/hiit->fitness (cardio). "
        "Intensity mapping: laag/rustig/low->light; matig/medium/moderate->moderate; hoog/hard/intense/high->intense. "
        "If duration is written as '1h' or '1 hour' return 60. If user writes '1 sessie' without minutes, duration_min should be null. "
        "Return null for anything you cannot infer confidently."
    )

    user = (
        f"Message: {user_text}\n"
        f"Known partial fields (may be null): {json.dumps(partial)}\n"
        "Return a JSON object that matches the schema."
    )

    try:
        client = _get_llm_client()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "WorkoutParse",
                    "strict": True,
                    "schema": WORKOUT_SCHEMA,
                },
            },
            temperature=0,
        )
        content = resp.choices[0].message.content
        data = json.loads(content) if isinstance(content, str) else {}
        # basic sanity
        if not isinstance(data, dict):
            return {}
        if data.get("confidence", 0) < 0.5:
            return {}
        return data
    except Exception:
        logger.exception("LLM interpret failed")
        return {}

# Supported exercise → MET by intensity
MET = {
    "swimming": {"light": 6.0, "moderate": 8.0, "intense": 10.0},
    "walking": {"light": 2.8, "moderate": 3.5, "intense": 4.5},
    "fitness (weights)": {"light": 3.5, "moderate": 4.5, "intense": 6.0},
    "fitness (cardio)": {"light": 5.5, "moderate": 7.0, "intense": 9.0},
    "cycling": {"light": 4.0, "moderate": 6.8, "intense": 10.0},
}

# English + Dutch aliases -> canonical MET keys
ALIASES = {
    # weights
    "weights": "fitness (weights)",
    "weight": "fitness (weights)",
    "weight training": "fitness (weights)",
    "kracht": "fitness (weights)",
    "krachttraining": "fitness (weights)",
    "gym": "fitness (weights)",
    # cardio
    "cardio": "fitness (cardio)",
    "hiit": "fitness (cardio)",
    "rennen": "fitness (cardio)",
    "hardlopen": "fitness (cardio)",
    # walking
    "walk": "walking",
    "walked": "walking",
    "walking": "walking",
    "wandelen": "walking",
    # swimming
    "swim": "swimming",
    "swimming": "swimming",
    "zwemmen": "swimming",
    # cycling
    "cycle": "cycling",
    "cycling": "cycling",
    "bike": "cycling",
    "fietsen": "cycling",
    "fiets": "cycling",
}

# Intensity (English + Dutch) -> canonical intensity
INTENSITY_MAP = {
    "low": "light",
    "light": "light",
    "laag": "light",
    "rustig": "light",
    "moderate": "moderate",
    "medium": "moderate",
    "matig": "moderate",
    "gemiddeld": "moderate",
    "high": "intense",
    "intense": "intense",
    "hoog": "intense",
    "hard": "intense",
    "zwaar": "intense",
}

# Words that often mean "1 session", not "1 minute"
SESSION_WORDS = {"sessie", "session", "workout", "training"}

# ---------- SHEETS (cached) ----------
_WS_CACHE = None

def _ws():
    global _WS_CACHE
    if _WS_CACHE is not None:
        return _WS_CACHE
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_JSON, scope)
    client = gspread.authorize(creds)
    sh = client.open(SPREADSHEET_NAME)
    _WS_CACHE = sh.get_worksheet(WORKSHEET_INDEX) or sh.sheet1
    return _WS_CACHE

def _ensure_header(ws):
    """Best-effort: make sure header row exists. Safe to call repeatedly."""
    try:
        rows = ws.get_all_values()
        if not rows:
            ws.append_row(["date", "exercise", "intensity", "duration_min", "calories", "user_id", "raw_text"])
            return
        # if header exists but shorter, don't mutate (avoid surprises); we just append extra columns.
    except Exception:
        # Don't fail bot because of header
        logger.exception("header check failed")

def log_to_google_sheets(date_iso, exercise_type, intensity, duration_min, calories, user_id: str, raw_text: str):
    ws = _ws()
    _ensure_header(ws)
    ws.append_row([date_iso, exercise_type, intensity, duration_min, round(calories), user_id, raw_text])

def get_daily_summary_text(user_id: Optional[str] = None) -> str:
    """If user_id is provided, returns per-user summary; otherwise total."""
    try:
        ws = _ws()
        rows = ws.get_all_values()
        today = dt.date.today().isoformat()
        total = 0.0
        count = 0
        minutes = 0
        for row in rows[1:]:
            if not row:
                continue
            if len(row) < 5:
                continue
            if row[0] != today:
                continue
            if user_id and len(row) >= 6 and str(row[5]) != str(user_id):
                continue
            try:
                minutes += int(float(row[3]))
            except Exception:
                pass
            try:
                total += float(row[4])
            except Exception:
                pass
            count += 1

        who = "your" if user_id else "today's"
        return (
            f"📊 *Summary ({who}):*\n"
            f"🏋️ Workouts: *{count}*\n"
            f"⏱ Minutes: *{minutes}*\n"
            f"🔥 Calories: *{round(total)} kcal*"
        )
    except Exception as e:
        logger.exception("summary error")
        return f"❌ Could not retrieve summary. Error: {e}"

def reset_today_rows(user_id: Optional[str] = None) -> int:
    ws = _ws()
    rows = ws.get_all_values()
    today = dt.date.today().isoformat()

    # rows are 1-indexed in delete_rows
    to_delete = []
    for i, row in enumerate(rows, start=1):
        if not row:
            continue
        if row[0] != today:
            continue
        if user_id:
            if len(row) >= 6 and str(row[5]) == str(user_id):
                to_delete.append(i)
        else:
            to_delete.append(i)

    for idx in reversed(to_delete):
        ws.delete_rows(idx)
    return len(to_delete)

def undo_last_for_user(user_id: str) -> bool:
    """Delete the most recent row for this user today."""
    ws = _ws()
    rows = ws.get_all_values()
    today = dt.date.today().isoformat()
    # Scan bottom-up
    for i in range(len(rows), 1, -1):  # skip header row at 1
        row = rows[i - 1]
        if not row:
            continue
        if len(row) < 6:
            continue
        if row[0] == today and str(row[5]) == str(user_id):
            ws.delete_rows(i)
            return True
    return False

# ---------- USER STATE ----------
def get_user_weight_kg(context: ContextTypes.DEFAULT_TYPE) -> float:
    try:
        return float(context.user_data.get("weight_kg", DEFAULT_WEIGHT_KG))
    except Exception:
        return DEFAULT_WEIGHT_KG

def get_pending(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
    pending = context.user_data.get("pending_workout")
    if not isinstance(pending, dict):
        pending = {}
        context.user_data["pending_workout"] = pending
    return pending

def clear_pending(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("pending_workout", None)

# ---------- UX: keyboards ----------
def kb_intensity():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("light"), KeyboardButton("moderate"), KeyboardButton("intense")],
            [KeyboardButton("laag"), KeyboardButton("matig"), KeyboardButton("hoog")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Choose intensity",
    )

def kb_duration():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("15 min"), KeyboardButton("30 min"), KeyboardButton("45 min"), KeyboardButton("60 min")],
            [KeyboardButton("1h"), KeyboardButton("90 min")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Enter duration",
    )

def kb_activity():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("walking"), KeyboardButton("cycling"), KeyboardButton("swimming")],
            [KeyboardButton("weights"), KeyboardButton("cardio")],
            [KeyboardButton("wandelen"), KeyboardButton("fietsen"), KeyboardButton("zwemmen")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Choose activity",
    )

# ---------- PARSER ----------
def _normalize_text(text: str) -> str:
    s = (text or "").lower().strip()
    # normalize separators
    s = re.sub(r"[,_;]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def parse_duration_minutes(s: str) -> Optional[int]:
    """Parse duration. Prefer explicit units. Avoid misreading '1 sessie ...' as 1 minute."""
    # 1h / 1 hour
    m = re.search(r"\b(\d{1,3})\s*(h|hr|hour|hours)\b", s)
    if m:
        try:
            return int(m.group(1)) * 60
        except Exception:
            return None

    # 45 min / 45m / 45 minutes
    m = re.search(r"\b(\d{1,4})\s*(m|min|mins|minute|minutes)\b", s)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None

    # plain number: only accept if it looks like a real workout duration
    # - ignore very small values (1-4) when session words are present
    m = re.search(r"\b(\d{1,4})\b", s)
    if m:
        try:
            val = int(m.group(1))
        except Exception:
            return None
        if val <= 4:
            # If they say "1 session" or similar, don't treat as minutes
            if any(w in s for w in SESSION_WORDS):
                return None
            # Otherwise, still suspicious: ask follow-up
            return None
        # If they wrote only "30 walking moderate", accept
        return val

    return None

def parse_intensity(s: str) -> Optional[str]:
    for token in s.split():
        if token in INTENSITY_MAP:
            return INTENSITY_MAP[token]
    # common pattern: "high intensity"
    if "intensity" in s:
        for k in ("light", "moderate", "medium", "high", "intense", "low", "laag", "matig", "hoog"):
            if k in s:
                return INTENSITY_MAP.get(k)
    return None

def parse_exercise(s: str) -> Optional[str]:
    # canonical keys
    for key in MET.keys():
        if key in s:
            return key
    # aliases
    for k, v in ALIASES.items():
        # word boundary for short tokens
        if re.search(rf"\b{re.escape(k)}\b", s):
            return v
    return None

def parse_workout(text: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    s = _normalize_text(text)
    dur = parse_duration_minutes(s)
    inten = parse_intensity(s)
    ex = parse_exercise(s)
    return ex, dur, inten

def estimate_calories(exercise: str, intensity: str, duration_min: int, weight_kg: float) -> float:
    met = MET[exercise][intensity]
    return met * weight_kg * (duration_min / 60.0)

def next_missing_question(pending: Dict[str, Any]) -> Tuple[Optional[str], Optional[ReplyKeyboardMarkup]]:
    if not pending.get("exercise"):
        return "Which activity? (walking / cycling / swimming / weights / cardio)", kb_activity()
    if not pending.get("duration_min"):
        return "How long was it? (e.g. 45 min, 1h)", kb_duration()
    if not pending.get("intensity"):
        return "What intensity? (light / moderate / intense)", kb_intensity()
    return None, None

# ---------- TELEGRAM HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to FitCoachBot!\n\n"
        "Just type something like:\n"
        "• `fietsen 45 min matig`\n"
        "• `swimming 30 minutes intense`\n"
        "• `weights 40 min moderate`\n\n"
        "If something is missing, I’ll ask one quick follow-up question.\n\n"
        "Commands: /summary /reset_day /setweight /undo /help",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardRemove(),
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️ *How to use FitCoachBot*\n\n"
        "*Log workouts (free text):*\n"
        "• `fietsen 45 min matig`\n"
        "• `cardio 30 min high`\n"
        "• `wandelen 60 min laag`\n\n"
        "*Commands:*\n"
        "• `/setweight 78` — set your weight\n"
        "• `/summary` — your totals today\n"
        "• `/reset_day` — remove *your* entries today\n"
        "• `/undo` — delete your last log today\n\n"
        "I support Dutch + English keywords. If anything is unclear, I’ll ask one question at a time.",
        parse_mode=ParseMode.MARKDOWN,
    )

async def setweight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            raise ValueError("missing")
        w = float(str(context.args[0]).replace(",", "."))
        if w < 30 or w > 250:
            raise ValueError("range")
        context.user_data["weight_kg"] = w
        await update.message.reply_text(f"✅ Saved your weight: *{w:.1f} kg*", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text("Usage: `/setweight 78`", parse_mode=ParseMode.MARKDOWN)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id) if update.effective_user else None
    await update.message.reply_text(get_daily_summary_text(user_id=uid), parse_mode=ParseMode.MARKDOWN)

async def reset_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = str(update.effective_user.id) if update.effective_user else None
        n = reset_today_rows(user_id=uid)
        clear_pending(context)
        await update.message.reply_text(f"✅ Removed {n} row(s) for today (your entries).", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.exception("reset_day error")
        await update.message.reply_text(f"❌ Could not reset today. Error: {e}", reply_markup=ReplyKeyboardRemove())

async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = str(update.effective_user.id) if update.effective_user else ""
        ok = undo_last_for_user(uid)
        if ok:
            await update.message.reply_text("↩️ Undid your last log for today.", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("Nothing to undo for today.", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.exception("undo error")
        await update.message.reply_text(f"❌ Could not undo. Error: {e}", reply_markup=ReplyKeyboardRemove())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    uid = str(update.effective_user.id) if update.effective_user else "unknown"

    try:
        # 1) Parse any fields from this message
        ex, dur, inten = parse_workout(text)

        pending = get_pending(context)
        # Merge parsed fields into pending state
        if ex:
            pending["exercise"] = ex
        if dur:
            pending["duration_min"] = dur
        if inten:
            pending["intensity"] = inten

        # Keep a raw text trail (helps debugging + undo auditing)
        pending["raw_text"] = (pending.get("raw_text", "") + " | " + text).strip(" |")

        # 2) If still missing something, try LLM interpretation once (optional)
        if LLM_ENABLED and (not pending.get("exercise") or not pending.get("duration_min") or not pending.get("intensity")):
            ai = await llm_interpret_workout(text, pending)
            if ai:
                if ai.get("exercise") and not pending.get("exercise"):
                    pending["exercise"] = ai["exercise"]
                if ai.get("duration_min") and not pending.get("duration_min"):
                    pending["duration_min"] = ai["duration_min"]
                if ai.get("intensity") and not pending.get("intensity"):
                    pending["intensity"] = ai["intensity"]

        # 3) If still missing something, ask ONE question + show buttons
        question, kb = next_missing_question(pending)
        if question:
            # A friendly confirmation of what we already got
            got = []
            if pending.get("exercise"):
                got.append(f"*{pending['exercise']}*")
            if pending.get("duration_min"):
                got.append(f"*{pending['duration_min']} min*")
            if pending.get("intensity"):
                got.append(f"*{pending['intensity']}*")
            got_line = f"I got: {', '.join(got)} ✅\n" if got else ""
            await update.message.reply_text(
                got_line + question,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb,
            )
            return

        # 3) We have everything -> log & clear pending
        exercise = pending["exercise"]
        duration_min = int(pending["duration_min"])
        intensity = pending["intensity"]

        # sanity check: avoid logging silly 0/1-minute entries accidentally
        if duration_min <= 4 and not re.search(r"\b(min|m|minute|minutes|h|hr|hour|hours)\b", _normalize_text(pending.get("raw_text", ""))):
            # Ask again instead of logging a likely mistake
            pending.pop("duration_min", None)
            question, kb = next_missing_question(pending)
            await update.message.reply_text(
                "Just to be sure — that duration looks very short. " + (question or "How many minutes?"),
                reply_markup=kb_duration(),
            )
            return

        weight = get_user_weight_kg(context)
        cal = estimate_calories(exercise, intensity, duration_min, weight)

        log_to_google_sheets(
            dt.date.today().isoformat(),
            exercise,
            intensity,
            duration_min,
            cal,
            uid,
            pending.get("raw_text", text),
        )

        clear_pending(context)

        await update.message.reply_text(
            f"✅ Logged: *{exercise}*, *{duration_min} min*, *{intensity}*\n"
            f"≈ *{round(cal)} kcal* (weight: {weight:.1f} kg)\n\n"
            f"Tip: use /undo if this was a mistake.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception:
        # Never show raw exception to user; keep it friendly.
        logger.exception("handle_message error (uid=%s, text=%r)", uid, text)
        await update.message.reply_text(
            "⚠️ Oops — something went wrong saving that. Please try again.\n"
            "If it keeps failing, type /help.",
            reply_markup=ReplyKeyboardRemove(),
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something unexpected happened. Please try again.",
            reply_markup=ReplyKeyboardRemove(),
        )

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("setweight", setweight))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("reset_day", reset_day))
    app.add_handler(CommandHandler("undo", undo))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
