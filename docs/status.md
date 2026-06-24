# Project Status

_Last updated: 2026-06-24_

## Current State

**Status:** Live and operational — deployed on Streamlit Community Cloud at
https://invoice-automation-sk.streamlit.app/ (auto-deploys from `main`).

The pipeline extracts invoice PDFs, matches them to PO records in the uploaded
Maintenance PO workbook, validates amounts/authorisation, and writes the updated
Excel back for download. Verified end-to-end (2026-06-24) against the real
`Maintenance PO's - 2026 TEST.xlsx`: 5 ILUX invoices (stated POs) auto-match, 2
invoices whose stated PO is absent fail with a clear "not found", and a PO-less
invoice would land in Needs Review (none in that set).

## What's Complete

- PDF extraction (generic multi-pattern + legacy supplier-specific extractors)
- **PO matching is PO-number-only for auto-update:** exact PO (cross-sheet) →
  invoice-number → fuzzy. Exact/invoice-number → Matched. A stated-but-missing PO
  → Failed. **A PO-less fuzzy (store+supplier+amount) hit → Needs Review, never
  auto** (it's a guess; clear "verify the PO" messaging). No similar/substring
  PO-number matching exists.
- **Store-name validation, shared across all extractors** — `store_registry.clean_store()`
  snaps a candidate to a real Menkind store (`data/known_stores.json`, 62 canonical
  names) or `""`; applied at the routing chokepoint so generic AND legacy
  (CJL/AAW/APS/Amazon) outputs are cleaned. Blank shows "Store: Unknown" and never
  fails a PO-matched invoice.
- Excel read/write with dynamic header detection; failed-sheet loads surfaced
- Streamlit three-column card UI (Matched / Review / Failed), confirmation flow
- **Design system** — `design-system/SPEC.md` (token source of truth) +
  `design-system/REVIEW.md` (audit). `GLOBAL_CSS` fully tokenised; WCAG 2.2 AA.
  Compact `.inv-note` callouts, thin 1px card accent, plain-English messages.
- **Config sections are read-only** — Supplier Nominal Codes + Store Names show a
  read-only list with a "contact Samuel" note (in-app edits don't persist on
  Streamlit Cloud; see Known Limitations). Nominal list is alphabetised.
- Amount validation: net+VAT==total reconciliation + PO cross-check (reviewable)
- Security hardening: HTML-escaped cards (XSS), Excel formula-injection guard,
  basename-only upload paths, specific exception handling + traceback logging
- UTF-8 on all report/config file writes (Windows cp1252 crash fix)
- Access-password gate (code present; **inactive until the secret is set**)
- Automated tests (standalone runner, no pytest) — 5 modules:
  `test_generic_extractor`, `test_matching`, `test_models`, `test_store_registry`,
  `test_report_generator`
- Report generation (CSV summary, text report); highlighted processed rows

## Recent Session (2026-06-24)

Design-system review/UI refinement (continued), then a batch of behaviour fixes.
All shipped to `main` and live. Commits (newest first):

- `8a7c3ca` Store-name validation applied to all extractors (shared `clean_store`)
- `c67f94d` PO-less fuzzy matches → Needs Review, never auto-update
- `3612bfe` UTF-8 report/config writes (fix Windows `UnicodeEncodeError`)
- `3fe1fe3` Combine About + Help into one concise section
- `98feb16` Alphabetise the Supplier Nominal Codes list
- `cc39ef0` Make nominal-code + store-name sidebar sections read-only
- `b1e71e5` Move store list to editable JSON registry (`data/known_stores.json`)
- `1362df2` Docs refresh
- `06a651c` Refine card UI (callouts, accent, messages) + accurate store extraction
- `eafa65a` / `f86d042` Design-system spec + tokenised `GLOBAL_CSS`

## To Resume

1. App is live and auto-deploys from `main` — no local run needed to use it.
2. Local dev: `.venv/Scripts/python.exe -m streamlit run web_app.py`.
3. Run tests: `.venv/Scripts/python.exe -m tests.test_matching` (and
   `test_models`, `test_generic_extractor`, `test_store_registry`,
   `test_report_generator`).
4. Test data lives in `C:\Users\samuel\OneDrive - Menkind\…\Sam\AI Invoice Test`
   (`Maintenance PO's - 2026 TEST.xlsx` + invoice PDFs). The repo's `example-files/`
   is an older set. The chrome-devtools browser tool can only read files inside the
   repo, so copy test files into the repo for a browser run, then delete them.
5. UI work: `design-system/SPEC.md` is the token source of truth.
6. **Next planned work:** persistence backend for the editable config lists
   (nominal codes + store names) so they're genuinely team-editable — in-app edits
   don't survive a redeploy. Options: Google Sheets (recommended) / Supabase /
   persistent-volume host. Brainstorm before building. Pairs with general sidebar
   polish. Also still outstanding: enable the access password (one secret).

## Known Limitations / Open Items

- **Access password is inactive** until `app_password` is set in Streamlit Cloud
  secrets — the deployed app is currently open to anyone with the link.
- **In-app config edits don't persist** — `data/nominal_codes.json` and
  `data/known_stores.json` are local files, but Streamlit Cloud's filesystem is
  ephemeral, so edits reset on redeploy. Both sections are therefore read-only in
  the app; durable changes = edit the JSON in the repo and push. A persistence
  backend is the next planned work.
- **Store list** is a static allow-list in `data/known_stores.json` (registry
  defaults are the fallback). A real store missing from it shows "Store: Unknown";
  fix = add it to the JSON.
- New suppliers need entries in `utils/supplier_registry.py`, `SheetSelector`,
  and the nominal-code mapping.
- Parsing is regex/label-based on flattened pdfplumber text — new supplier
  formats / merged-column layouts need new patterns (see CLAUDE.md gotchas).
- `CJLExtractor` mis-reads VAT on `286301.pdf` (£20 vs £1,736.40) — pre-existing,
  that invoice fails on PO-not-found anyway.
- Amount fields remain `Decimal` (0 = zero/unread); a full `Optional[Decimal]`
  migration was deliberately deferred.
- Tests use a standalone runner; pytest is not installed/configured.
