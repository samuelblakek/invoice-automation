# Project Status

_Last updated: 2026-06-23_

## Current State

**Status:** Live and operational — deployed on Streamlit Community Cloud at
https://invoice-automation-sk.streamlit.app/ (auto-deploys from `main`).

The pipeline extracts invoice PDFs, matches them to PO records in the uploaded
Maintenance PO workbook, validates amounts/authorisation, and writes the updated
Excel back for download. Verified end-to-end on the live app with the colleague
test batch: all 5 ILUX invoices auto-match; invoices whose stated PO is absent
from the workbook correctly report "not found".

## What's Complete

- PDF extraction (generic multi-pattern + legacy supplier-specific extractors)
- PO matching: exact (cross-sheet) → invoice-number → fuzzy (PO-less only)
- Excel read/write with dynamic header detection; failed-sheet loads surfaced
- Streamlit three-column card UI (Matched / Review / Failed), confirmation flow
- Nominal code mapping (JSON-backed, sidebar-editable, multi-code disambiguation)
- Amount validation: net+VAT==total reconciliation + PO cross-check (reviewable)
- Security hardening: HTML-escaped cards (XSS), Excel formula-injection guard,
  basename-only upload paths, specific exception handling + traceback logging
- Access-password gate (code present; **inactive until the secret is set**)
- Automated tests (standalone runner, no pytest framework):
  `tests/test_generic_extractor.py`, `tests/test_matching.py`, `tests/test_models.py`
- Report generation (CSV summary, text report); highlighted processed rows

## Recent Session (2026-06-22 → 2026-06-23)

Resumed from a pause to fix a reported extraction failure, then ran a full
multi-agent review and acted on it. Commits (newest first):

- `4d93713` Track: enable access password on live app (deferred)
- `4d08bb9` Access-password gate + model-invariant refactor (Invoice/PORecord
  `__post_init__`, `has_po`/`has_store`, ValidationResult derived properties)
- `ed6d0d5` Review fixes: amount reconciliation, XSS + formula-injection guards,
  specific exception handling/logging, exact-PO matching, VAT/NET regex, tests
- `923d5c2` Tighten fuzzy matching: stated-but-missing PO reports "not found"
- `36e0d50` Stop caching extractor instances (stale code after redeploy)
- `c6a0d6d` ILUX store/PO extraction + cross-sheet PO matching
- `40c01d1` Invoice-number (`INV-` filenames) + amount/glyph extraction fixes

## To Resume

1. App is live and auto-deploys from `main` — no local run needed to use it.
2. Local dev: `pip install -r requirements.txt` then `streamlit run web_app.py`.
3. Run tests: `.venv/Scripts/python.exe -m tests.test_generic_extractor`
   (and `tests.test_matching`, `tests.test_models`).
4. See `tasks/todo.md` — the top item (enable the access password) needs a
   one-line secret added in Streamlit Cloud.

## Known Limitations / Open Items

- **Access password is inactive** until `app_password` is set in Streamlit Cloud
  secrets — the deployed app is currently open to anyone with the link.
- New suppliers need entries in `utils/supplier_registry.py`, `SheetSelector`,
  and the nominal-code mapping.
- Parsing is regex/label-based on flattened pdfplumber text — new supplier
  formats / merged-column layouts need new patterns (see CLAUDE.md gotchas).
- `CJLExtractor` mis-reads VAT on `286301.pdf` (£20 vs £1,736.40) — pre-existing,
  that invoice fails on PO-not-found anyway.
- Amount fields remain `Decimal` (0 = zero/unread); a full `Optional[Decimal]`
  migration was deliberately deferred.
- Tests use a standalone runner; pytest is not installed/configured.
