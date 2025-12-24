# Invoicing Project (Excel → Word/PDF)

Dit project genereert facturen **automatisch** vanuit een Excel bestand naar **Word (.docx)** en optioneel **PDF**.

## Bestanden
- `facturen.xlsx` – input (tabbladen: **Facturen** en **Regels**)
- `template.docx` – Word template met placeholders
- `generate.py` – generator script
- `out/` – output map voor gegenereerde facturen

## Excel structuur

### Tabblad: Facturen (1 rij per factuur)
Kolommen (Nederlandstalig):
- `Factuurnummer`
- `Factuurdatum`
- `Vervaldatum`
- `Debiteurnummer` (optioneel)
- `Klantnaam`
- `Straat + huisnr`
- `Postcode + Plaats`

### Tabblad: Regels (meerdere regels per factuur)
- `Factuurnummer`
- `Omschrijving`
- `Leverdatum`
- `Aantal`
- `Eenheid`
- `Tarief`
- `BTW_percentage`

## Installeren
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Genereren (Word)
```bash
python generate.py
```
De Word facturen komen in `out/`.

## PDF (optioneel)
De makkelijkste manier is met LibreOffice (headless):
```bash
soffice --headless --convert-to pdf --outdir out out/*.docx
```

## Template placeholders
In `template.docx` worden o.a. deze placeholders gebruikt:
- `{{FACTUURNR}}`, `{{DEBITEURNR}}`, `{{FACTUURDATUM}}`, `{{VERVALDATUM}}`
- `{{KLANT_NAAM}}`, `{{KLANT_ADRES}}`, `{{KLANT_POSTCODE_PLAATS}}`
- `{{TOTAAL_EXCL}}`, `{{BTW_TOTAAL}}`, `{{TOTAAL_INCL}}`
