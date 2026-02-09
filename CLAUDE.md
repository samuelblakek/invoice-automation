# Invoice Processing Automation

## Architecture

**Entry points:**
- `web_app.py` — Streamlit web interface (primary)
- `main.py` — CLI alternative

**Package structure** (`invoice_automation/`):
- `extractors/` — PDF data extraction (generic + supplier-specific)
  - `generic_extractor.py` — Handles any supplier via multi-pattern matching (primary)
  - `aaw_extractor.py`, `cjl_extractor.py`, `aps_extractor.py`, `amazon_extractor.py` — Legacy supplier-specific extractors
  - `base_extractor.py` — Abstract base class for all extractors
- `processors/` — Excel reading (`excel_reader.py`), writing, sheet selection (`sheet_selector.py`)
- `validators/` — PO matching (`po_matcher.py`), amount validation, authorization checks
- `models/` — Data classes: `InvoiceData`, `PORecord`, `ValidationResult`
- `utils/` — Helpers (amount parsing, text normalization)
- `reports/` — Report generation (CSV summary, text report)
- `config/` — YAML configuration loading

## How to Run

```bash
pip install -r requirements.txt
streamlit run web_app.py
```

## How to Test

Process example PDFs in `example-files/` against the test Excel file (`Maintenance PO's - TEST.xlsx`). All 7 test invoices should extract and match correctly.

```bash
python main.py process --input-dir example-files --dry-run
```

## Key Patterns

- **Generic extraction** — The generic extractor uses multi-pattern matching (regex cascades) to handle any supplier format. No supplier-name checks in extraction logic — patterns match field labels and text structure, not supplier identity.
- **Multi-strategy PO matching** — Three strategies tried in order: exact PO match, invoice number search, then fuzzy multi-field matching (store + amount + supplier).
- **Excel header detection** — Headers are at row 5-6, not row 0. The reader scans for the header row dynamically by looking for known column names (PO, STORE, etc.).
- **Billing city exclusion** — When extracting store/delivery address, known billing HQ cities (e.g. "Dorking" for Menkind) and duplicate cities are excluded to find the actual delivery location.
- **Sheet selection** — Supplier name maps to the correct Excel sheet (e.g. CJL -> "CJL", Amazon -> "ORDERS", generic -> "OTHER").

## Gotchas

- **pdfplumber merges columns** — Multi-column PDF layouts (Customer Address | Delivery Address) become single merged lines. Don't assume addresses are on separate lines.
- **VAT regex needs `.\d{2}`** — Patterns like `VAT\s+£?\s*(\d+)` are too broad and match dates. Always require decimal format `\.\d{2}` for currency amounts.
- **PO cells have embedded newlines** — CJL sheet has values like `\nCJL408\n`. Use substring/contains matching, not exact comparison. Strip and normalize before matching.
- **Excel headers at row 5-6, not row 0** — The Maintenance PO workbook has 4-5 rows of title/color-legend before the actual header row.
- **PO is optional** — Not all invoices have PO numbers. The pipeline handles PO-less invoices via fuzzy matching fallback.
- **No AI/LLM tokens used** — The app is entirely rule-based (regex, fuzzy string matching, pandas). Claude Code wrote the code but the running app uses zero AI.

## Lessons

See `tasks/lessons.md` for accumulated patterns and corrections from development.
