# Project Status

## Current State

**Status:** Working — clean codebase, ready to resume

The invoice processing pipeline is operational. PDFs are extracted, matched against PO records, validated, and written back to the Maintenance PO spreadsheet with nominal codes populated automatically.

## What's Complete

- PDF extraction (generic multi-pattern + legacy supplier-specific extractors)
- PO matching (exact → invoice number search → fuzzy multi-field)
- Excel read/write with dynamic header detection
- Streamlit web app with three-column card UI (Matched / Review / Failed)
- Confirmation flow for near-miss invoices
- Nominal code mapping — persisted in `data/nominal_codes.json`, editable in sidebar, multi-code supplier support with work-type disambiguation
- Warning system for missing PO, high-value invoices, unmapped nominal codes
- Report generation (CSV summary, text report)
- Excel output with highlighted processed rows

## Recent Session (2026-02-11)

Ran full code quality analysis (lint, tech debt, best practices, performance) and fixed all issues:
- Created `utils/supplier_registry.py` — single source of truth for supplier identification (eliminates triplicated logic)
- Added sheet caching to ExcelReader for performance
- Removed 370+ lines of dead code across 6 utility/extractor files
- Fixed type annotations throughout (any/object -> Optional[datetime], bare tuples -> parameterized, etc.)
- Replaced print() with logging, added error handling to nominal code I/O
- Removed unused dependencies (click, pyyaml)
- All imports verified, ruff passes clean

Previous session focused on nominal code persistence and matching:
- Moved nominal codes from session-state-only to JSON-file-backed storage
- Removed cost centre file dependency
- Fixed sidebar UI (replaced broken data_editor with compact list + controls)
- Built smart matching: space-stripped comparison, first-word fallback, work-type scoring for multi-code suppliers

## To Resume

1. `pip install -r requirements.txt` (if deps changed)
2. `streamlit run web_app.py`
3. Upload test PDFs from `example-files/` and a Maintenance PO spreadsheet
4. See `tasks/todo.md` for possible future work

## Known Limitations

- New suppliers need entries in `utils/supplier_registry.py`, `SheetSelector.SUPPLIER_SHEET_MAP`, and the nominal code mapping in the sidebar
- Work-type disambiguation relies on word overlap between mapping descriptions and invoice PDF text — very short descriptions may not differentiate well
- No automated tests — verification is manual via the web app with example PDFs
