// src/telegramBot.js
import "dotenv/config";
import TelegramBot from "node-telegram-bot-api";
import fs from "fs";
import path from "path";
import Tesseract from "tesseract.js";
import { runAccountingAgent } from "./accountingAgent.js";
import { appendInvoiceRow } from "./googleSheets.js";

// ---------------------------------------------------------
// TELEGRAM SETUP
// ---------------------------------------------------------

const token = process.env.TELEGRAM_BOT_TOKEN;

if (!token) {
  console.error("⚠️ TELEGRAM_BOT_TOKEN missing in .env!");
  process.exit(1);
}

const bot = new TelegramBot(token, { polling: true });

console.log("🤖 Telegram Accounting Agent bot is running...");

// Simple in-memory state per chat
// { mode: "idle" | "awaiting_manual_invoice" }
const userStates = new Map();

// ---------------------------------------------------------
// OCR FUNCTION
// ---------------------------------------------------------

async function runOcr(imagePath) {
  console.log("🔍 Running OCR on:", imagePath);

  const { data } = await Tesseract.recognize(imagePath, "eng");
  return data.text;
}

// ---------------------------------------------------------
// HANDLE INCOMING MESSAGES
// ---------------------------------------------------------

bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const state = userStates.get(chatId) || { mode: "idle" };

  // 1) If we are waiting for manual invoice input, handle that first
  if (state.mode === "awaiting_manual_invoice" && msg.text && !msg.photo) {
    await handleManualInvoiceInput(chatId, msg.text);
    return;
  }

  // 2) If it's a photo, treat as invoice image
  if (msg.photo && msg.photo.length > 0) {
    try {
      await handlePhotoMessage(msg);
    } catch (err) {
      console.error("❌ Error during photo handling:", err);
      bot.sendMessage(
        chatId,
        "Er ging iets mis tijdens het verwerken van de foto."
      );
    }
    return;
  }

  // 3) Normal commands / default text behaviour
  if (msg.text === "/start") {
    userStates.set(chatId, { mode: "idle" });
    bot.sendMessage(
      chatId,
      "Welkom bij je Accounting Agent! 📊\n\n" +
        "Stuur me een foto van een factuur, dan haal ik de bedragen, btw en leverancier eruit.\n\n" +
        "Als de foto onduidelijk is, vraag ik je om de gegevens handmatig in te vullen."
    );
  } else {
    bot.sendMessage(chatId, "Stuur me een foto van een factuur 📷.");
  }
});

// ---------------------------------------------------------
// PHOTO HANDLING
// ---------------------------------------------------------

async function handlePhotoMessage(msg) {
  const chatId = msg.chat.id;

  const photos = msg.photo;
  const largestPhoto = photos[photos.length - 1];
  const fileId = largestPhoto.file_id;

  console.log("📷 Received photo, file_id:", fileId);

  const file = await bot.getFile(fileId);
  const filePath = file.file_path;

  const fileUrl = `https://api.telegram.org/file/bot${token}/${filePath}`;
  const res = await fetch(fileUrl);

  if (!res.ok) {
    throw new Error("Failed to download image from Telegram.");
  }

  const buffer = Buffer.from(await res.arrayBuffer());

  const tmpDir = path.join(process.cwd(), "src/tmp");
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });

  const localFilePath = path.join(
    tmpDir,
    `invoice_${chatId}_${Date.now()}.jpg`
  );
  fs.writeFileSync(localFilePath, buffer);

  console.log("💾 Saved image:", localFilePath);

  await bot.sendMessage(
    chatId,
    "Factuur ontvangen 📄\nIk ben bezig met verwerken…"
  );

  // STEP 1 — OCR
  const ocrText = await runOcr(localFilePath);
  console.log("🧾 OCR resultaat (eerste 300 tekens):\n", ocrText.slice(0, 300));

  // STEP 2 — Accounting Agent (OpenAI)
  const invoiceData = await runAccountingAgent(ocrText);

  // Decide if the result is reliable or not
  const lowConfidence =
    invoiceData.confidence_overall < 0.6 ||
    !invoiceData.vendor ||
    invoiceData.amount_incl_vat === 0;

  if (lowConfidence) {
    // 🔴 FALLBACK: ask user to resend or fill manually
    userStates.set(chatId, { mode: "awaiting_manual_invoice" });

    const confPct = (invoiceData.confidence_overall * 100).toFixed(0);

    const fallbackMsg = `
❗ Ik kon deze factuur niet goed uitlezen.
Mijn zekerheid is laag (${confPct}%).

Je kunt:
1️⃣ Een nieuwe, scherpere foto sturen
of
2️⃣ De belangrijkste gegevens zelf invullen.

Als je zelf wilt invullen, stuur dan één bericht in dit formaat:

\`Leverancier | Factuurnummer | Datum (YYYY-MM-DD) | Bedrag incl. btw | Btw-bedrag | Categorie\`

Voorbeeld:
\`TechSupplies BV | TS-2025-0041 | 2025-01-14 | 12.10 | 2.10 | Office/Hardware\`
`;

    await bot.sendMessage(chatId, fallbackMsg, { parse_mode: "Markdown" });
    return;
  }

  // STEP 3 — Normal success reply
  const reply = `
📄 *Factuur verwerkt!*

*Leverancier:* ${invoiceData.vendor}
*Factuurnummer:* ${invoiceData.invoice_number ?? "-"}
*Datum:* ${invoiceData.date}

💰 *Bedrag incl. btw:* €${invoiceData.amount_incl_vat}
💶 *Bedrag excl. btw:* €${invoiceData.amount_excl_vat}
🧾 *Btw:* €${invoiceData.vat_amount} (${invoiceData.vat_rate})

📦 *Categorie:* ${invoiceData.category} / ${invoiceData.subcategory}

🔎 Confidence: ${(invoiceData.confidence_overall * 100).toFixed(0)}%
`;

  await bot.sendMessage(chatId, reply, { parse_mode: "Markdown" });

  // Store in Google Sheets
  try {
    const dataForSheet = {
      ...invoiceData,
      processing_mode: "automatic",
    };
    await appendInvoiceRow(chatId, dataForSheet);
  } catch (err) {
    console.error("❌ Failed to store invoice in Google Sheets:", err);
  }

  // back to idle state
  userStates.set(chatId, { mode: "idle" });
}

// ---------------------------------------------------------
// MANUAL INPUT HANDLER (FALLBACK)
// ---------------------------------------------------------

async function handleManualInvoiceInput(chatId, text) {
  // Expecting:
  // Leverancier | Factuurnummer | Datum (YYYY-MM-DD) | Bedrag incl. btw | Btw-bedrag | Categorie

  const parts = text.split("|").map((p) => p.trim());

  if (parts.length !== 6) {
    await bot.sendMessage(
      chatId,
      "Ik kon dit niet goed lezen 🤔.\n\n" +
        "Stuur het alsjeblieft in dit formaat:\n" +
        "`Leverancier | Factuurnummer | Datum (YYYY-MM-DD) | Bedrag incl. btw | Btw-bedrag | Categorie`",
      { parse_mode: "Markdown" }
    );
    return;
  }

  const [
    vendor,
    invoiceNumber,
    dateStr,
    amountInclStr,
    vatAmountStr,
    category,
  ] = parts;

  const amountIncl = Number(amountInclStr.replace(",", "."));
  const vatAmount = Number(vatAmountStr.replace(",", "."));
  const amountExcl = +(amountIncl - vatAmount).toFixed(2);

  if (Number.isNaN(amountIncl) || Number.isNaN(vatAmount)) {
    await bot.sendMessage(
      chatId,
      "De bedragen konden niet als nummers worden gelezen. Gebruik bijvoorbeeld: `12.10` of `669.13`.",
      { parse_mode: "Markdown" }
    );
    return;
  }

  // Very rough VAT rate guess
  let vatRate = "onbekend";
  if (amountExcl > 0) {
    const rate = (vatAmount / amountExcl) * 100;
    if (Math.abs(rate - 21) < 1) vatRate = "21%";
    else if (Math.abs(rate - 9) < 1) vatRate = "9%";
    else if (Math.abs(rate - 0) < 1) vatRate = "0%";
    else vatRate = `${rate.toFixed(1)}%`;
  }

  const invoiceData = {
    vendor,
    invoice_number: invoiceNumber || null,
    date: dateStr,
    description: "Handmatig ingevoerde factuurgegevens via Telegram",
    amount_incl_vat: amountIncl,
    amount_excl_vat: amountExcl,
    vat_rate: vatRate,
    vat_amount: vatAmount,
    currency: "EUR",
    category,
    subcategory: "",
    payment_method: null,
    notes: "Handmatig ingevuld door gebruiker na mislukte OCR/LLM.",
    confidence_overall: 1.0,
    processing_mode: "manual",
  };

  // Confirm to user
  const reply = `
✔️ Ik heb de factuur handmatig verwerkt.

*Leverancier:* ${invoiceData.vendor}
*Factuurnummer:* ${invoiceData.invoice_number ?? "-"}
*Datum:* ${invoiceData.date}

💰 *Bedrag incl. btw:* €${invoiceData.amount_incl_vat}
💶 *Bedrag excl. btw:* €${invoiceData.amount_excl_vat}
🧾 *Btw:* €${invoiceData.vat_amount} (${invoiceData.vat_rate})

📦 *Categorie:* ${invoiceData.category}
`;

  await bot.sendMessage(chatId, reply, { parse_mode: "Markdown" });

  // Store manual invoice in Google Sheets
  try {
    await appendInvoiceRow(chatId, invoiceData);
  } catch (err) {
    console.error("❌ Failed to store manual invoice in Google Sheets:", err);
  }

  // reset state
  userStates.set(chatId, { mode: "idle" });
}
