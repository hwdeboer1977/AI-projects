// src/googleSheets.js
import "dotenv/config";
import fs from "fs";
import path from "path";
import { GoogleSpreadsheet } from "google-spreadsheet";

const SPREADSHEET_ID = process.env.GOOGLE_SHEETS_INVOICES_ID;
const KEY_FILE = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_FILE;

if (!SPREADSHEET_ID) {
  console.error("⚠️ GOOGLE_SHEETS_INVOICES_ID missing in .env");
}
if (!KEY_FILE) {
  console.error("⚠️ GOOGLE_SERVICE_ACCOUNT_KEY_FILE missing in .env");
}

// Resolve key file path relative to project root
const keyFilePath = path.resolve(KEY_FILE);

let serviceAccountCreds = null;
try {
  const jsonStr = fs.readFileSync(keyFilePath, "utf8");
  serviceAccountCreds = JSON.parse(jsonStr);
} catch (err) {
  console.error("❌ Failed to read/parse service account key file:", err);
}

const doc = new GoogleSpreadsheet(SPREADSHEET_ID);

async function getDocAuthed() {
  if (!serviceAccountCreds) {
    throw new Error("Service account credentials not loaded");
  }

  await doc.useServiceAccountAuth(serviceAccountCreds);
  await doc.loadInfo();
  return doc;
}

// Get or create a monthly sheet named "Invoices December 2025"
async function getOrCreateMonthlySheet(invoiceDate) {
  const d = invoiceDate ? new Date(invoiceDate) : new Date();

  const monthName = d.toLocaleString("en-US", { month: "long" });
  const year = d.getFullYear();
  const title = `Invoices ${monthName} ${year}`;

  const doc = await getDocAuthed();

  let sheet = doc.sheetsByTitle[title];
  if (!sheet) {
    sheet = await doc.addSheet({
      title,
      headerValues: [
        "timestamp_processed",
        "chat_id",
        "vendor",
        "invoice_number",
        "invoice_date",
        "description",
        "amount_excl_vat",
        "vat_amount",
        "vat_rate",
        "amount_incl_vat",
        "currency",
        "category",
        "subcategory",
        "payment_method",
        "confidence_overall",
        "processing_mode",
      ],
    });
    console.log(`🆕 Created new sheet: ${title}`);
  }

  return sheet;
}

export async function appendInvoiceRow(chatId, invoiceData) {
  const sheet = await getOrCreateMonthlySheet(invoiceData.date);

  const processingMode = invoiceData.processing_mode || "automatic";

  await sheet.addRow({
    timestamp_processed: new Date().toISOString(),
    chat_id: chatId,
    vendor: invoiceData.vendor || "",
    invoice_number: invoiceData.invoice_number ?? "",
    invoice_date: invoiceData.date || "",
    description: invoiceData.description || "",
    amount_excl_vat: invoiceData.amount_excl_vat ?? "",
    vat_amount: invoiceData.vat_amount ?? "",
    vat_rate: invoiceData.vat_rate || "",
    amount_incl_vat: invoiceData.amount_incl_vat ?? "",
    currency: invoiceData.currency || "EUR",
    category: invoiceData.category || "",
    subcategory: invoiceData.subcategory || "",
    payment_method: invoiceData.payment_method ?? "",
    confidence_overall: invoiceData.confidence_overall ?? "",
    processing_mode: processingMode,
  });

  console.log(`✅ Invoice stored in Google Sheet tab "${sheet.title}"`);
}
