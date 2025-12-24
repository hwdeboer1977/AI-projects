from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "invoice_ai_out"
OUT_DIR.mkdir(exist_ok=True)

TWO = Decimal("0.01")


# ----------------------------
# Helpers
# ----------------------------
def to_date(x: Any) -> Optional[date]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x).strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def iso(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def dec(x: Any) -> Optional[Decimal]:
    if x is None or x == "":
        return None
    try:
        return Decimal(str(x))
    except Exception:
        return None


def money_eur(x: Decimal) -> str:
    q = x.quantize(TWO, rounding=ROUND_HALF_UP)
    return f"€{q:.2f}".replace(".", ",")


def strip_code_fences(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rsplit("```", 1)[0]
    return s.strip()


def call_llm_text(client: OpenAI, model: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return (resp.choices[0].message.content or "").strip()


def call_llm_json(client: OpenAI, model: str, prompt: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    raw = strip_code_fences(raw)
    return json.loads(raw)


# ----------------------------
# Data model (minimal)
# ----------------------------
@dataclass
class InvoiceHeader:
    factuurnummer: str
    factuurdatum: Optional[date]
    vervaldatum: Optional[date]
    debiteurnummer: str
    klantnaam: str
    klant_adres: str
    klant_postcode_plaats: str


@dataclass
class InvoiceLine:
    factuurnummer: str
    omschrijving: str
    datum: Optional[date]
    aantal_uren: Optional[Decimal]
    tarief: Optional[Decimal]
    btw_pct: Optional[Decimal]


# ----------------------------
# Excel loading (expects sheets: Facturen, Regels)
# ----------------------------
def load_excel(path: Path) -> Tuple[List[InvoiceHeader], List[InvoiceLine]]:
    wb = load_workbook(path, data_only=True)
    inv_ws = wb["Facturen"]
    reg_ws = wb["Regels"]

    inv_header = [c.value for c in next(inv_ws.iter_rows(min_row=1, max_row=1))]
    reg_header = [c.value for c in next(reg_ws.iter_rows(min_row=1, max_row=1))]

    def row_to_dict(header: List[Any], row: Tuple[Any, ...]) -> Dict[str, Any]:
        d = {}
        for i, key in enumerate(header):
            if key is None:
                continue
            d[str(key).strip()] = row[i] if i < len(row) else None
        return d

    invoices: List[InvoiceHeader] = []
    for row in inv_ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        d = row_to_dict(inv_header, row)

        invoices.append(
            InvoiceHeader(
                factuurnummer=str(d.get("Factuurnummer") or "").strip(),
                factuurdatum=to_date(d.get("Factuurdatum")),
                vervaldatum=to_date(d.get("Vervaldatum")),
                debiteurnummer=str(d.get("Debiteurnummer") or "").strip(),
                klantnaam=str(d.get("Klantnaam") or "").strip(),
                klant_adres=str(d.get("Straat + huisnr") or "").strip(),
                klant_postcode_plaats=str(d.get("Postcode + Plaats") or "").strip(),
            )
        )

    lines: List[InvoiceLine] = []
    for row in reg_ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        d = row_to_dict(reg_header, row)

        # Accept column names you mentioned:
        # - "Datum"
        # - "Aantal uren"
        # - "Tarief"
        # - "BTW_percentage"
        lines.append(
            InvoiceLine(
                factuurnummer=str(d.get("Factuurnummer") or "").strip(),
                omschrijving=str(d.get("Omschrijving") or "").strip(),
                datum=to_date(d.get("Datum")),
                aantal_uren=dec(d.get("Aantal uren")),
                tarief=dec(d.get("Tarief")),
                btw_pct=dec(d.get("BTW_percentage")),
            )
        )

    return invoices, lines


def group_lines(lines: List[InvoiceLine]) -> Dict[str, List[InvoiceLine]]:
    out: Dict[str, List[InvoiceLine]] = {}
    for ln in lines:
        out.setdefault(ln.factuurnummer, []).append(ln)
    return out


# ----------------------------
# AI prompts (inline for v1)
# ----------------------------
def build_rewrite_prompt(inv: InvoiceHeader, lines: List[InvoiceLine]) -> str:
    # Build a deterministic raw summary from Excel
    # (AI will rewrite it to polished invoice text)
    items = []
    for ln in lines:
        dt = iso(ln.datum) or ""
        hrs = f"{ln.aantal_uren}".replace(".", ",") if ln.aantal_uren is not None else ""
        items.append(f"- {dt}: {hrs} uur — {ln.omschrijving}")

    raw = "\n".join(items)

    return f"""
Je schrijft een nette, zakelijke factuur-omschrijving in het Nederlands voor een ZZP IT/consultancy factuur.
Maak een korte kopregel en daarna maximaal 3 bullets. Houd het professioneel en concreet.

Klant: {inv.klantnaam}
Factuurnummer: {inv.factuurnummer}

Ruwe input (uit Excel):
{raw}

Geef ALLEEN de tekst terug (geen code fences).
""".strip()


def build_audit_prompt(inv: InvoiceHeader, lines: List[InvoiceLine], totals: Dict[str, str], omschrijving: str) -> str:
    payload = {
        "factuurnummer": inv.factuurnummer,
        "factuurdatum": iso(inv.factuurdatum),
        "vervaldatum": iso(inv.vervaldatum),
        "debiteurnummer": inv.debiteurnummer,
        "klantnaam": inv.klantnaam,
        "klant_adres": inv.klant_adres,
        "klant_postcode_plaats": inv.klant_postcode_plaats,
        "regels": [
            {
                "datum": iso(ln.datum),
                "aantal_uren": float(ln.aantal_uren) if ln.aantal_uren is not None else None,
                "tarief": float(ln.tarief) if ln.tarief is not None else None,
                "btw_pct": float(ln.btw_pct) if ln.btw_pct is not None else None,
                "omschrijving": ln.omschrijving,
            }
            for ln in lines
        ],
        "totals": totals,
        "omschrijving": omschrijving,
    }

    return f"""
Je bent een strenge auditor voor Nederlandse ZZP facturen.
Controleer op ontbrekende velden, inconsistenties en onduidelijke omschrijving.
Geef ALLEEN JSON terug met exact dit schema:

{{
  "status": "OK" | "WARNING" | "ERROR",
  "warnings": [string],
  "errors": [string],
  "suggestions": [string]
}}

Data:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Regels:
- ERROR bij ontbrekende klantnaam, factuurdatum, of geen regels.
- WARNING bij btw_pct niet 0/9/21, of lege omschrijving, of uren/tarief 0.
- Suggestion: korte verbetering (max 3).

ALLEEN JSON (geen code fences).
""".strip()


# ----------------------------
# Deterministic totals
# ----------------------------
def compute_totals(lines: List[InvoiceLine]) -> Dict[str, str]:
    net_total = Decimal("0.00")
    vat_total = Decimal("0.00")

    for ln in lines:
        if ln.aantal_uren is None or ln.tarief is None:
            continue
        net = (ln.aantal_uren * ln.tarief).quantize(TWO, rounding=ROUND_HALF_UP)
        net_total += net
        if ln.btw_pct is not None:
            vat = (net * (ln.btw_pct / Decimal("100"))).quantize(TWO, rounding=ROUND_HALF_UP)
            vat_total += vat

    gross = (net_total + vat_total).quantize(TWO, rounding=ROUND_HALF_UP)

    return {
        "totaal_excl": money_eur(net_total),
        "btw_totaal": money_eur(vat_total),
        "totaal_incl": money_eur(gross),
    }


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        raise SystemExit("❌ OPENAI_API_KEY ontbreekt in invoice-ai/.env")

    parser = argparse.ArgumentParser(description="invoice-ai v1 (Excel-first): rewrite + audit")
    parser.add_argument("--excel", required=True, help="Pad naar facturen.xlsx")
    parser.add_argument("--factuur", default=None, help="Factuurnummer (optioneel). Anders: alle facturen.")
    args = parser.parse_args()

    excel_path = Path(args.excel).resolve()
    if not excel_path.exists():
        raise SystemExit(f"❌ Excel niet gevonden: {excel_path}")

    invoices, lines = load_excel(excel_path)
    lines_by = group_lines(lines)

    # Select invoices
    selected = invoices
    if args.factuur:
        selected = [inv for inv in invoices if inv.factuurnummer == args.factuur]
        if not selected:
            raise SystemExit(f"❌ Factuurnummer niet gevonden in tabblad 'Facturen': {args.factuur}")

    client = OpenAI(api_key=api_key)

    for inv in selected:
        inv_lines = lines_by.get(inv.factuurnummer, [])
        if not inv_lines:
            print(f"⚠️  {inv.factuurnummer}: geen regels gevonden → audit zal ERROR zijn.")
            inv_lines = []

        totals = compute_totals(inv_lines)

        # 1) Rewrite
        rewrite_prompt = build_rewrite_prompt(inv, inv_lines)
        omschrijving = call_llm_text(client, model, rewrite_prompt)

        # 2) Audit
        audit_prompt = build_audit_prompt(inv, inv_lines, totals, omschrijving)
        try:
            audit = call_llm_json(client, model, audit_prompt)
        except Exception as e:
            # if model returned non-JSON, save raw
            raw_path = OUT_DIR / f"{inv.factuurnummer}.audit_raw.txt"
            raw_path.write_text(str(e), encoding="utf-8")
            raise

        # Write outputs
        (OUT_DIR / f"{inv.factuurnummer}.rewrite.txt").write_text(omschrijving, encoding="utf-8")
        (OUT_DIR / f"{inv.factuurnummer}.audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        print(f"✅ {inv.factuurnummer}")
        print(f"   - rewrite: {OUT_DIR / (inv.factuurnummer + '.rewrite.txt')}")
        print(f"   - audit:   {OUT_DIR / (inv.factuurnummer + '.audit.json')}")
        print(f"   - status:  {audit.get('status')}")

        if audit.get("warnings"):
            for w in audit["warnings"]:
                print(f"   ⚠️ {w}")
        if audit.get("errors"):
            for er in audit["errors"]:
                print(f"   ❌ {er}")


if __name__ == "__main__":
    main()
