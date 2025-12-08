# AgentAI_Public

A collection of smart AI-powered Python agents for daily life automation — from tracking fitness and nutrition to logging data into Google Sheets.

## 📂 Contents

### `Fitness_agent.py`

Logs your workouts (swimming, walking, cardio, weights) and calories burned into a Google Sheet via Telegram.

### `Nutrition_agent.py`

Logs your meals (e.g. `"1 banana"`) with macros (calories, protein, fat, carbs) into a Google Sheet via Telegram.

## 🚀 Getting Started

### 🔧 Requirements

- Python 3.12 (recommended; Python 3.13 not yet fully supported)
- Install dependencies:

```bash
pip install -r requirements.txt
```

### ⚙️ Environment Variables (`.env`)

Create a `.env` file in the project root with:

```
# Telegram bot tokens
TELEGRAM_BOT_TOKEN_FITNESS=your_telegram_fitness_token
TELEGRAM_BOT_TOKEN_NUTRITION=your_telegram_nutrition_token

# OpenAI
OPENAI_API_KEY_HW=your_openai_api_key

# Optional: override service account JSON path
GOOGLE_SERVICE_ACCOUNT_JSON=C:/full/path/to/your-service-account.json
```

### 📑 Google Sheets Setup

1. **Enable APIs** in Google Cloud Console:
   - Google Sheets API
   - Google Drive API
2. **Create a Service Account** and download the JSON key file (looks like `nutritionbot-...json`).
3. Place the file in your project root **or** point to it via `GOOGLE_SERVICE_ACCOUNT_JSON` in `.env`.
4. Open your Google Sheet (e.g. `Calories_log`) and **share it** with the service account email (ends in `iam.gserviceaccount.com`) as **Editor**.
5. Ensure the worksheet names match the code:
   - `Calories_log` spreadsheet
   - `Calories` worksheet

## 🏃‍♀️ Run Agents

Run each bot from the repo root:

```bash
.\.venv\Scripts\Activate.ps1
python src/Fitness_agent.py
python src/Nutrition_agent.py
```

Then talk to the bots on Telegram:

- **FitnessBot**:

  ```
  swimming 45 minutes at moderate intensity
  ```

- **NutritionBot**:
  ```
  2 eggs and toast
  ```

Both will log entries into your linked Google Sheet ✅

## 📊 Google Sheets Integration

All logs are stored in your personal Google Sheets (`Fitness_log`, `Calories_log`), making it easy to analyze progress over time.

## 📌 Author

[@hwdeboer1977](https://github.com/hwdeboer1977) — Powered by **OpenAI, Telegram, Google Sheets, and Python bots ⚡**  
Contributions and forks welcome!
