# AI Accounting Agent

A fully automated, AI-powered accounting workflow that extracts data from invoices, calculates VAT, categorizes expenses, and stores results in Google Sheets — all through a Telegram bot interface.

This project combines:

- **OCR (image → text)**
- **LLM-based invoice parsing**
- **VAT & category logic**
- **Fallback dialogue for unclear invoices**
- **Automatic saving of results to Google Sheets**
- **Telegram as a lightweight mobile interface**

Perfect for freelancers who want simple, fast, automated bookkeeping.

---

## ⭐ Features

### ✔️ Upload invoices via Telegram

Send a picture or screenshot of any invoice directly to your bot.

### ✔️ OCR + AI parsing

Extracts:

- Vendor
- Invoice number
- Date
- Amount incl./excl. VAT
- VAT rate + VAT amount
- Category & subcategory
- Confidence score

### ✔️ Dutch VAT logic

Supports:

- 21%
- 9%
- 0%  
  Automatically computes excl. VAT.

### ✔️ Automatic fallback dialogue

If OCR/AI confidence is low, the bot asks the user to either:

- Send a clearer photo
- OR enter invoice details manually in one line

### ✔️ Saves structured data to Google Sheets

Creates monthly tabs automatically, such as:

- `Invoices December 2025`
- `Invoices January 2026`

Each invoice becomes a row in the correct monthly sheet.

### ✔️ Local JSON output

Parsed invoices are saved in `src/output/` for debugging.

---

# 📁 Project Structure

```
AI-Accounting-Agent/
│
├── .env
├── package.json
├── src/
│   ├── accountingAgent.js
│   ├── googleSheets.js
│   ├── telegramBot.js
│   ├── data/
│   ├── output/
│   ├── tmp/
│   └── tools/
└── README.md
```

---

# 🧠 Script Overview

## 1. `src/accountingAgent.js` — LLM extraction engine

Handles AI parsing of invoice text using OpenAI’s Responses API.

Responsibilities:

- Receives raw OCR text
- Sends to LLM with enforced schema
- Extracts vendor, dates, amounts, VAT, categories
- Generates a confidence score
- Saves parsed invoice as JSON in `/src/output`

This is the core "reasoning engine" of the project.

---

## 2. `src/googleSheets.js` — Google Sheets storage layer

Responsibilities:

- Authenticate via Google Service Account
- Open spreadsheet by ID
- Create monthly sheets automatically
- Append invoice rows in consistent format
- Safe handling of private key (via `.env` or `.pem`)

This script provides persistent storage.

---

## 3. `src/telegramBot.js` — Telegram interface & workflow

Handles:

- Receiving images
- Downloading invoice photos
- OCR preprocessing + extraction
- Calling `accountingAgent.js`
- Fallback dialogue on low confidence
- Saving validated invoices to Google Sheets
- Managing per-user workflow state

Acts as the user interface of the Accounting Agent.

---

# 🔧 Requirements

Install dependencies:

```
npm install
```

Included packages:

- node-telegram-bot-api
- openai
- tesseract.js
- google-spreadsheet
- dotenv

---

# 🔐 Environment Variables (`.env`)

```
TELEGRAM_BOT_TOKEN=123456:ABCDEF
OPENAI_API_KEY=your_openai_key_here

GOOGLE_SHEETS_INVOICES_ID=your_spreadsheet_id
GOOGLE_SERVICE_ACCOUNT_EMAIL=service-account@project-id.iam.gserviceaccount.com

# Either:
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# OR recommended:
GOOGLE_PRIVATE_KEY_FILE=src/service-account-private-key.pem
```

---

# ▶️ Running the Bot

Start your Telegram bot with:

```
node src/telegramBot.js
```

Make sure:

- `.env` is configured correctly
- Service account has **Editor** access to the spreadsheet

Then open Telegram and type:

```
/start
```

Upload an invoice photo and your Accounting Agent processes it fully automatically.

---

# 🚀 Future Improvements

- Google Vision OCR for better clarity
- Vendor memory + smarter category prediction
- `/vat-summary` command
- `/month YYYY-MM` overview command
- CSV/XLSX export
- Multi-user support for commercial offering
- Cloud deployment

---

# 📄 License

MIT — free to use and modify.
