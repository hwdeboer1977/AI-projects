# invoice-ai (v1)

AI layer on top of deterministic invoicing.

This module takes **invoice data from Excel** (via `invoice-deterministic`) and enriches it with AI:

- ✨ Clean, professional invoice descriptions
- 🔍 Automatic audit / QA (VAT, dates, consistency)
- 🧠 Suggestions for improvement
- ❌ No recalculation of amounts by AI (Excel remains the source of truth)

---

## What invoice-ai explicitly does NOT do

- ❌ No price or VAT calculations
- ❌ No modification of Excel files
- ❌ No invoice generation (handled by `invoice-deterministic`)

AI is used **only for interpretation, text quality, and control**.

---

## Architecture (deliberately separated)

```
AI-Invoice/
│
├── invoice-deterministic/     # Hard logic (Excel → Word/PDF)
│   ├── facturen.xlsx
│   ├── generate.py
│
├── invoice-ai/                # AI enrichment & audit
│   ├── invoice_ai.py
│   ├── schemas/
│   │   ├── invoice.schema.json
│   │   └── audit.schema.json
│   ├── prompts/
│   │   ├── rewrite.txt
│   │   └── audit.txt
│   └── invoice_ai_out/
│       ├── *.rewrite.txt
│       └── *.audit.json
```

---

## Installation

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Make sure your `.env` contains a valid OpenAI API key:

```env
OPENAI_API_KEY=sk-...
```

---

## Usage (recommended – Excel as source)

```bash
python invoice_ai.py \
  --excel ../invoice-deterministic/facturen.xlsx \
  --factuur BS-2025-12-001
```

---

## Output

### Rewrite (human-readable)

`invoice_ai_out/BS-2025-12-001.rewrite.txt`

### Audit (machine / compliance)

`invoice_ai_out/BS-2025-12-001.audit.json`

---

## Optional: free-text parsing (experimental)

```bash
python invoice_ai.py --text "6 hours Wix events testing 12 Dec 2025 80 EUR per hour VAT 21 client Interactive Monkey"
```

⚠️ Not recommended for production. Excel remains the source of truth.

---

## Design philosophy

- Deterministic where correctness matters
- AI only where it adds real value
- Audit-first, professional-grade design
