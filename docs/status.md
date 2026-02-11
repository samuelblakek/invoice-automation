# Project Status

## Current State

**Status:** Working — tested and functional

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

Focused on nominal code persistence and matching:
- Moved nominal codes from session-state-only to JSON-file-backed storage
- Removed cost centre file dependency
- Fixed sidebar UI (replaced broken data_editor with compact list + controls)
- Built smart matching: space-stripped comparison, first-word fallback, work-type scoring for multi-code suppliers
- All 21 suppliers mapped and tested

## Known Limitations

- Supplier name matching depends on the generic extractor's `_identify_supplier()` output — new suppliers may need entries added to both the extractor and the nominal code mapping
- Work-type disambiguation relies on word overlap between mapping descriptions and invoice PDF text — very short descriptions may not differentiate well
- No automated tests — verification is manual via the web app with example PDFs
