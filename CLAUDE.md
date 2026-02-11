# Invoice Processing Automation

## Architecture

**Entry point:** `web_app.py` — Streamlit web interface

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

**Data files:**
- `data/nominal_codes.json` — Supplier→nominal code mapping (persisted, editable via sidebar)

## How to Run

```bash
pip install -r requirements.txt
streamlit run web_app.py
```

## How to Test

Process example PDFs in `example-files/` against the test Excel file (`Maintenance PO's - TEST.xlsx`) via the web app. Upload the PDFs and Excel files, click Process, and verify all 7 test invoices extract and match correctly.

## Key Patterns

- **Generic extraction** — The generic extractor uses multi-pattern matching (regex cascades) to handle any supplier format. No supplier-name checks in extraction logic — patterns match field labels and text structure, not supplier identity.
- **Multi-strategy PO matching** — Three strategies tried in order: exact PO match, invoice number search, then fuzzy multi-field matching (store + amount + supplier).
- **Excel header detection** — Headers are at row 5-6, not row 0. The reader scans for the header row dynamically by looking for known column names (PO, STORE, etc.).
- **Billing city exclusion** — When extracting store/delivery address, known billing HQ cities (e.g. "Dorking" for Menkind) and duplicate cities are excluded to find the actual delivery location.
- **Sheet selection** — Supplier name maps to the correct Excel sheet (e.g. CJL -> "CJL", Amazon -> "ORDERS", generic -> "OTHER").
- **Nominal code mapping** — Persisted in `data/nominal_codes.json`, loaded into session state on startup. The sidebar expander shows all mappings and supports add/remove with save-to-disk. Codes are 4-digit numbers only (e.g. `7820`, not `7820 Stores Repairs`).
- **Nominal code lookup** — `lookup_nominal_code()` in `web_app.py` handles: (1) substring matching with space-stripping (so `LampShopOnline` matches `Lamp Shop Online`), (2) first-word fallback, (3) multi-code suppliers — when a supplier has multiple entries with different work types (suffix after ` - `), the function scores each work description against the invoice text to pick the correct code. A warning is shown on the card when no mapping is found.

## Gotchas

- **pdfplumber merges columns** — Multi-column PDF layouts (Customer Address | Delivery Address) become single merged lines. Don't assume addresses are on separate lines.
- **VAT regex needs `.\d{2}`** — Patterns like `VAT\s+£?\s*(\d+)` are too broad and match dates. Always require decimal format `\.\d{2}` for currency amounts.
- **PO cells have embedded newlines** — CJL sheet has values like `\nCJL408\n`. Use substring/contains matching, not exact comparison. Strip and normalize before matching.
- **Excel headers at row 5-6, not row 0** — The Maintenance PO workbook has 4-5 rows of title/color-legend before the actual header row.
- **PO is optional** — Not all invoices have PO numbers. The pipeline handles PO-less invoices via fuzzy matching fallback.
- **No AI/LLM tokens used** — The app is entirely rule-based (regex, fuzzy string matching, pandas). Claude Code wrote the code but the running app uses zero AI.
- **Supplier name mismatch** — The generic extractor's `_identify_supplier()` returns names like `"LampShopOnline"` or `"MetSafe"`, which may not match the mapping table's `"Lamp Shop Online"` or `"Metro Security (UK) Limited (MetSafe)"`. The lookup handles this via space-stripped comparison, but new suppliers may need entries in both the extractor and the mapping.
- **Cost centre file removed** — The Cost Centre Summary uploader was removed. Nominal codes come from JSON, and `ExcelReader.cost_centre_path` is now optional (defaults to `None`).

## UI / Styling

- **Layout**: V3 card board -- three-column (Matched / Review / Failed) with sidebar file uploaders
- **Font**: Outfit (Google Fonts) -- single family for headings + body
- **Palette**: Dark slate/navy (#0F1923 bg) with glassmorphism (rgba + backdrop-blur) cards
- **Texture**: Layered radial gradients with subtle blue/purple colour glow, SVG noise/grain overlay, frosted glass cards + sidebar
- **CSS**: All styling in GLOBAL_CSS constant at top of web_app.py, injected via st.markdown() -- uses ::after pseudo-element on .stApp for noise overlay (pointer-events: none)
- **Streamlit theme**: .streamlit/config.toml must stay in sync with CSS colour tokens
- **Icon fonts**: Material Symbols Rounded used by Streamlit for expander/sidebar icons -- font override rules must preserve these (see CSS comments)

## Lessons

See `tasks/lessons.md` for accumulated patterns and corrections from development.
