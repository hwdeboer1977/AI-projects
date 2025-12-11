// src/accountingAgent.js
import "dotenv/config";
import OpenAI from "openai";
import fs from "fs";
import path from "path";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/* ---------------------------------------------------------
   SYSTEM PROMPT
--------------------------------------------------------- */

const systemPrompt = `
You are an accounting extraction agent for a Dutch freelancer.

You receive the full text of a single invoice or receipt.
Your task is to:
- Parse the vendor, invoice number (if any), date, description, total amount incl. VAT, currency, and payment method.
- Infer reasonable values if something is slightly ambiguous.
- Compute the VAT amount, VAT rate and amount excl. VAT using Dutch VAT rules (21%, 9%, 0%).
- Assign a bookkeeping category and subcategory (e.g. "Office" / "Hardware").
- Estimate an overall confidence score between 0 and 1.

You MUST respond with a single JSON object in this exact structure:

{
  "vendor": string,
  "invoice_number": string | null,
  "date": "YYYY-MM-DD",
  "description": string,
  "amount_incl_vat": number,
  "amount_excl_vat": number,
  "vat_rate": string,
  "vat_amount": number,
  "currency": "EUR",
  "category": string,
  "subcategory": string,
  "payment_method": string | null,
  "notes": string,
  "confidence_overall": number
}

Do NOT include extra fields.
Do NOT explain anything.
`;

/* ---------------------------------------------------------
   JSON SCHEMA
--------------------------------------------------------- */

const invoiceSchema = {
  type: "object",
  properties: {
    vendor: { type: "string" },
    invoice_number: { type: ["string", "null"] },
    date: { type: "string" },
    description: { type: "string" },
    amount_incl_vat: { type: "number" },
    amount_excl_vat: { type: "number" },
    vat_rate: { type: "string" },
    vat_amount: { type: "number" },
    currency: { type: "string" },
    category: { type: "string" },
    subcategory: { type: "string" },
    payment_method: { type: ["string", "null"] },
    notes: { type: "string" },
    confidence_overall: { type: "number" },
  },
  required: [
    "vendor",
    "invoice_number",
    "date",
    "description",
    "amount_incl_vat",
    "amount_excl_vat",
    "vat_rate",
    "vat_amount",
    "currency",
    "category",
    "subcategory",
    "payment_method",
    "notes",
    "confidence_overall",
  ],
  additionalProperties: false,
};

/* ---------------------------------------------------------
   MAIN FUNCTION (USED BY TELEGRAM BOT)
--------------------------------------------------------- */

export async function runAccountingAgent(invoiceText) {
  const response = await client.responses.create({
    model: "gpt-4.1-mini",
    input: [
      { role: "system", content: systemPrompt },
      { role: "user", content: invoiceText },
    ],
    text: {
      format: {
        type: "json_schema",
        name: "invoice_record",
        schema: invoiceSchema,
        strict: true,
      },
    },
  });

  const jsonStr = response.output_text;

  let obj;
  try {
    obj = JSON.parse(jsonStr);
  } catch (err) {
    console.error("❌ Failed to parse JSON:", err);
    throw new Error("Could not parse invoice JSON");
  }

  // Save output to file
  const outputDir = path.join(process.cwd(), "src/output");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const safeVendor = (obj.vendor || "unknown")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

  const safeDate = (obj.date || "unknown-date").replace(/[^0-9-]/g, "");

  const fileName = `invoice_${safeVendor}_${safeDate}.json`;
  const filePath = path.join(outputDir, fileName);

  fs.writeFileSync(filePath, JSON.stringify(obj, null, 2), "utf8");
  console.log(`💾 Saved parsed invoice to: ${filePath}`);

  return obj;
}
