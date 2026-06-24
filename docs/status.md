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
- **Store extraction with allow-list validation** — returns a real Menkind store
  name (validated against `_KNOWN_STORES`, 62 canonical names from the workbook)
  or `""`; never a street/address guess. Blank shows "Store: Unknown" and never
  fails a PO-matched invoice.
- Excel read/write with dynamic header detection; failed-sheet loads surfaced
- Streamlit three-column card UI (Matched / Review / Failed), confirmation flow
- **Design system** — `design-system/SPEC.md` (canonical token source of truth) +
  `design-system/REVIEW.md` (audit). `GLOBAL_CSS` fully tokenised; WCAG 2.2 AA.
- **Refined card UI** — compact `.inv-note` callouts (calm text + coloured icon),
  thin 1px card accent, plain-English validation messages.
- Nominal code mapping (JSON-backed, sidebar-editable, multi-code disambiguation)
- Amount validation: net+VAT==total reconciliation + PO cross-check (reviewable)
- Security hardening: HTML-escaped cards (XSS), Excel formula-injection guard,
  basename-only upload paths, specific exception handling + traceback logging
- Access-password gate (code present; **inactive until the secret is set**)
- Automated tests (standalone runner, no pytest framework):
  `tests/test_generic_extractor.py`, `tests/test_matching.py`, `tests/test_models.py`
- Report generation (CSV summary, text report); highlighted processed rows

## Recent Session (2026-06-23)

Design-system review + UI refinement + store-extraction accuracy. The store work
ran in parallel (separate agent) against the real Maintenance PO workbook. All
shipped to `main` and live. Commits (newest first):

- `06a651c` Refine card UI (callouts, accent, messages) + accurate store extraction
- `eafa65a` Note ui-design-review branch + design-system in status.md
- `f86d042` Tokenise GLOBAL_CSS and add design-system spec (SPEC.md + REVIEW.md)

Earlier session (2026-06-22 → 23): `4d93713` access-password tracking ·
`4d08bb9` access-password gate + model-invariant refactor · `ed6d0d5` review
fixes (amount/XSS/formula-injection/error-handling/tests) · `923d5c2` tighten
fuzzy matching · `36e0d50` stop caching extractors · `c6a0d6d` ILUX store/PO +
cross-sheet matching · `40c01d1` invoice-number + amount/glyph fixes.

## To Resume

1. App is live and auto-deploys from `main` — no local run needed to use it.
2. Local dev: `pip install -r requirements.txt` then `streamlit run web_app.py`
   (or `.venv/Scripts/python.exe -m streamlit run web_app.py`).
3. Run tests: `.venv/Scripts/python.exe -m tests.test_generic_extractor`
   (and `tests.test_matching`, `tests.test_models`).
4. UI work: `design-system/SPEC.md` is the token source of truth — add a `:root`
   token + spec entry rather than hardcoding, and use the QA checklist at the
   bottom of `SPEC.md` as a self-review.
5. **Next piece of work:** persistence overhaul for the editable config lists —
   in-app edits to **nominal codes** and **store names** don't survive a redeploy
   (Streamlit Cloud's filesystem is ephemeral), so a team-editable list needs an
   external store (Google Sheets / Supabase, or move host). Also: optimise/improve
   the sidebar generally. To be brainstormed before building.
6. Still outstanding: enable the access password (one-line secret in Streamlit Cloud).

## Known Limitations / Open Items

- **Access password is inactive** until `app_password` is set in Streamlit Cloud
  secrets — the deployed app is currently open to anyone with the link.
- **In-app config edits don't persist** — both `data/nominal_codes.json` and
  `data/known_stores.json` are written to a local file, but Streamlit Cloud's
  filesystem is ephemeral, so sidebar edits reset on redeploy. Durable changes
  are made by editing the JSON in the repo (the "Store Names" UI says to contact
  Samuel). A proper persistence backend is the next planned work.
- **Store list** — recognised stores live in `data/known_stores.json` (registry
  defaults are the fallback). A real invoice town that isn't a Menkind store
  correctly returns "" ("Store: Unknown") rather than guessing.
- New suppliers need entries in `utils/supplier_registry.py`, `SheetSelector`,
  and the nominal-code mapping.
- Parsing is regex/label-based on flattened pdfplumber text — new supplier
  formats / merged-column layouts need new patterns (see CLAUDE.md gotchas).
- `CJLExtractor` mis-reads VAT on `286301.pdf` (£20 vs £1,736.40) — pre-existing,
  that invoice fails on PO-not-found anyway.
- Amount fields remain `Decimal` (0 = zero/unread); a full `Optional[Decimal]`
  migration was deliberately deferred.
- Tests use a standalone runner; pytest is not installed/configured.
