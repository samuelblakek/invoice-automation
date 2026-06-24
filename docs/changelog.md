# Changelog

## 2026-06-24 — Store list moved to editable JSON (registry)

- The recognised-store list moved from a hardcoded constant in
  `generic_extractor.py` to `data/known_stores.json`, loaded via a new
  `invoice_automation/utils/store_registry.py` (single source of truth, with the
  62 canonical names + alias map as defaults/fallback). The extractor reads it
  per-instance, so edits take effect on the next Process.
- Sidebar gained a "Store Names" section (an `st.data_editor` table). **Known
  limitation:** Streamlit Cloud's filesystem is ephemeral, so in-app edits don't
  persist across redeploys — the section carries a note to contact Samuel, and
  durable changes are made by editing `data/known_stores.json` in the repo. The
  same limitation applies to `data/nominal_codes.json`; a persistence overhaul
  for both is the next piece of work.
- Added `tests/test_store_registry.py` (load/save round-trip, case-insensitive
  dedupe, blank-drop, missing/corrupt-file fallback, alias preservation).
- **Follow-up (same day):** both config sections (Supplier Nominal Codes + Store
  Names) were made **read-only** — a "contact Samuel" note plus a read-only list —
  since in-app edits don't persist on Streamlit Cloud. The editable UI was
  removed until a persistent backend lands (tracked in `tasks/todo.md`).

## 2026-06-23 — Design system, UI refinement, accurate store extraction

Shipped to `main` (live). Commits `f86d042`, `eafa65a`, `06a651c`.

- **Design system:** added `design-system/SPEC.md` (canonical three-layer token
  source of truth) and `design-system/REVIEW.md` (audit against the
  `sk-design-system-framework`). Refactored `web_app.py` `GLOBAL_CSS` so every
  value references a `:root` token (spacing/radius/shadow/typography/motion/
  colour/focus) — the only raw values outside `:root` are `0` and the grain SVG.
- **Accessibility (WCAG 2.2 AA):** muted text `#64748B` → `#7C8BA1` (was 3.42:1,
  now 4.70:1 on cards); added `:focus-visible` rings (`--ring #38BDF8`),
  `:active`/`:disabled` states, 44px touch targets, and a `prefers-reduced-motion`
  block. `.streamlit/config.toml` colours unchanged (already in sync).
- **Card UI refinement:**
  - Wall-of-colour warnings/errors replaced by a compact `.inv-note` callout —
    calm `--text-secondary` body text, status carried only by the ⚠ icon colour,
    thin top divider (built by `inv_note_html()`).
  - Thin **1px** low-contrast left accent (muted `--green-border`/`--red-border`)
    instead of the chunky 3px saturated stripe.
  - Validation messages rewritten to plain English; removed the unhelpful
    "closest/similar PO" suggestions from not-found errors (matching is
    direct-match only — the candidate scan still drives PO-less fuzzy matching).
- **Store extraction accuracy:** `_extract_store_location` now returns a clean
  Menkind store name or `""` — never a street/address fragment. Candidates are
  validated against `_KNOWN_STORES` (62 canonical names sourced from the real
  Maintenance PO workbook: data-sheet STORE columns + the two pivot tabs, "PB"
  rows excluded, typos normalised), with a `_STORE_ALIASES` map for short forms
  (e.g. `Silverburn` → `Glasgow Silverburn`). Longest-match-wins preserves real
  branch qualifiers (Lower/Upper/Fort). A blank store renders "Store: Unknown ⚠"
  and never fails a PO-matched invoice (the store check is gated on `has_store`).
  Examples: "Kings Inch Road" → Braehead; Sunbelt's "Taunton" → "" (a delivery
  town, not a Menkind store — no false guess). `test_generic_extractor` expanded.

## 2026-06-22 — Access password + model invariant refactor

- **Auth:** the app is now gated behind a shared access password read from
  Streamlit secrets (`app_password`). Set it under Manage app → Settings →
  Secrets to enable; if unset (local dev) the app stays open. Constant-time
  comparison. `.streamlit/secrets.toml.example` documents the key. For per-user
  identity, `st.login` (OIDC) is the future upgrade path.
- **Model invariants (type refactor):**
  - `Invoice.__post_init__` rejects a blank `invoice_number` and coerces the
    three money fields to `Decimal`, locking the "money is Decimal" invariant.
  - Added `Invoice.has_po` / `has_store` helpers; `POMatcher` now uses them
    instead of ad-hoc truthiness (a real £0 amount and whitespace-only fields
    are handled consistently).
  - `ValidationResult.is_valid` / `can_auto_update` / `errors` / `warnings` are
    now derived `@property`s instead of stored fields written by `finalize()` —
    removing the "read before finalize() returns a wrong False" hazard and the
    errors/warnings desync. `finalize()` is now a no-op kept for compatibility.
  - `PORecord.__post_init__` guards `row_index >= 0` (it addresses the row that
    gets written back).
  - Added `tests/test_models.py`.

## 2026-06-22 — Review fixes: correctness, security, error handling, tests

Acting on a multi-agent code/security/app review:

- **Amount correctness:** added a net + VAT = total reconciliation check (and an
  optional cross-check against the PO's recorded amount). A mismatch is now a
  reviewable error — the invoice goes to Review for confirmation instead of
  auto-posting a likely mis-read amount. A £0 amount no longer reports
  "no authorization required".
- **Matching:** PO lookup is now exact-per-line instead of substring, so a
  truncated PO (`OT040`) can't match a different longer PO (`OT0402`).
- **Robustness:** a maintenance sheet that exists but fails to load is surfaced
  as a UI banner (`ExcelReader.load_warnings`) instead of silently making every
  PO on it "not found"; absent optional sheets stay quiet (debug-level).
- **Extraction:** broadened the VAT lookbehind (`exc`/`excl`/`ex.`) and required
  decimals in the broad NET fallback so "Net 30 days" can't become net=30.
- **Security:** HTML-escaped all PDF-derived fields rendered in result cards
  (stored-XSS fix) and guarded the Excel write-back against formula injection
  (`= + - @` prefixes). Uploaded filenames are reduced to their basename.
- **Error handling:** the per-invoice handler now catches `PDFExtractionError`
  for the user-facing card and logs unexpected exceptions with a full traceback
  under a distinct message, so a bug no longer masquerades as a bad PDF.
- **Tests:** added `tests/test_matching.py` (PO strategies, cross-sheet fallback,
  not-found guard, exact-vs-substring, fuzzy-only-for-PO-less, amount
  reconciliation) with a generated `.xlsx` fixture.

## 2026-06-22 — Tighten fuzzy matching: stated-but-missing PO reports "not found"

When an invoice states a PO that isn't in any maintenance sheet, the matcher no
longer falls back to fuzzy-matching a *different* PO (which risked invoicing
against the wrong order). `POMatcher` Strategy 3 fuzzy matching now runs only for
invoices with **no PO of their own**; when an invoice has a PO that exact-match
(Strategy 1) and invoice-number (Strategy 2) both miss, it reports
"PO '<x>' was not found in any maintenance sheet — not matched", listing the
closest store/amount candidates only as a manual-lookup hint. PO-less invoices
keep the existing fuzzy behaviour.

Also: removed `@st.cache_resource` from `get_extractors()` so extractor code
changes take effect on every redeploy (the cache previously served stale
extractor instances until a manual reboot).

## 2026-06-22 — Fix: ILUX store/PO extraction + cross-sheet PO matching

Surfaced by a live test of the colleague's batch (all 5 ILUX invoices extracted
but none matched). Three fixes so ILUX invoices match their PO records:

- **Store** was read from the footer ("Registered in England No: …") because
  ILUX's `Site Address` block comes through column-merged/garbled. Added a
  high-priority `Menkind - <Store>` pattern (handles multi-word stores like
  "Milton Keynes", "Meadowhall Lower").
- **PO** kept the ticket prefix: "Order number 123352/LUX004" extracted as
  `123352/LUX004`. Added an `Order number (?:<ticket>/)?<PO>` pattern → `LUX004`,
  `OT0402`.
- **Sheet routing:** ILUX POs span two sheets (`OT…` on OTHER, `LUX…` on the
  `ILUX` sheet), but the matcher only searched the one mapped sheet — and the
  `ILUX` sheet wasn't even in `load_maintenance_sheets`. Added `ILUX` to the
  maintenance-sheet list and a cross-sheet exact-PO fallback
  (`find_po_record_any_sheet`): try the mapped sheet first, then the others.

Result: all 5 ILUX invoices match correctly (OT0402/Trafford, LUX010/Meadowhall,
LUX004/Chelmsford, LUX009/Derby, LUX008/Milton Keynes), store match ≥77%. Added
store/PO regression tests. Example invoices unchanged (stores now resolve to
clean names; amounts still balance).

Known, not code bugs: PO `CJL319` (286301) and `OT0329` (29120566) aren't in the
2026 test workbook (older POs); the fuzzy fallback can still propose a wrong PO
when the real one is absent, but flags it via a low store-match score.

## 2026-06-22 — Fix: hyphenated `INV-NNNNN` filenames failed extraction

- **Bug:** Invoices named `INV-10801.pdf` (and similar) raised "Could not extract
  invoice number from <file>" when no in-PDF invoice-number pattern matched. The
  filename fallback in `GenericExtractor._extract_invoice_number` used the regex
  `INV(\d+)`, which requires digits *immediately* after `INV` and so missed any
  separator (`INV-10801`, `INV_10801`, `INV 10801`).
- **Fix:** Fallback regex is now `INV([-_ ]?)(\d+)` — the separator is optional;
  a hyphen/underscore is preserved in the result, whitespace is dropped.
- Added `tests/test_generic_extractor.py` as a regression guard (runs standalone
  or under pytest). Verified all 7 example invoices still extract unchanged.

- **Also found & fixed (same ILUX files):** VAT was being read off the net line
  `Total ex VAT £115.00` by the broad last-resort `\bVAT\b` pattern, so VAT equalled
  net (e.g. INV-10801 reported VAT £115.00 instead of £23.00). Added a `Total Tax`
  pattern (ILUX's current template) and a `(?<!ex )` lookbehind on the broad pattern.
  All 5 ILUX invoices now satisfy net + VAT = total.

- **Corrupted `£` glyph in invoice total:** one supplier's font emits the ASCII
  `f.` for `£`, so `INVOICE TOTAL f.1212.00` was skipped and the broad pattern
  grabbed `SUB TOTAL 1010.00` as the total instead. Total patterns now accept
  `£` or `f.`. `example-files/Invoice 37712.1383.pdf` now reports total £1212.00
  (was £1010.00); all example invoices satisfy net + VAT = total.

## 2026-02-11 — Code Cleanup & Tech Debt Removal

- Ran lint (ruff), tech debt, best practices, and performance scans across the codebase
- **High-severity fixes:**
  - Created `utils/supplier_registry.py` as single source of truth for supplier identification (was triplicated across GenericExtractor, web_app.py, and extractors)
  - Added `_sheet_cache` to ExcelReader to avoid redundant disk I/O during matching
  - Fixed `ValidationResult.nominal_code` — added as proper dataclass field (was monkey-patched at runtime)
  - Fixed unscoped `store_text` variable in APS extractor
- **Dead code removal (370+ lines):**
  - Removed 5 unused methods + PO_PATTERNS from StringMatcher
  - Removed 4 unused methods from BaseExtractor
  - Removed 4 unused methods + AMOUNT_PATTERN from AmountParser
  - Removed 3 unused methods from DateParser
  - Removed 4 dead methods from ExcelReader (load_codes_sheet, load_cost_centre_summary, load_nominal_code_mapping, get_store_list)
- **Type annotation fixes:**
  - Replaced `-> any` / `-> object` with `-> Optional[datetime]` in all extractors
  - Replaced bare `-> tuple` with parameterized tuples throughout
  - Fixed `-> int` to `-> Optional[int]` in ExcelWriter header/column finders
  - Replaced `Any` with `Optional[str]` in Validation model
  - Added return type to `ValidationResult.create_error`
- **Other improvements:**
  - Replaced all `print()` calls with `logging` module in ExcelReader and ExcelWriter
  - Added error handling to nominal code JSON load/save
  - Removed unused dependencies (click, pyyaml) from requirements.txt
  - Fixed unused exception variables flagged by ruff

## 2026-02-11 — Nominal Code Persistence & Matching

- Nominal code mapping now persisted in `data/nominal_codes.json` — survives resets, page refreshes, and doesn't require re-uploading the cost centre file
- Removed Cost Centre Summary file uploader (no longer needed)
- Replaced buggy `data_editor` widget with a compact sidebar UI: scrollable bordered list, text inputs for adding, selectbox for removing
- Added visible success feedback (green banner) when adding or removing suppliers
- Text inputs clear after adding a supplier
- Nominal codes stripped to 4-digit numbers only (no text suffixes)
- Supplier names cleaned up to title case
- Lookup now handles multi-code suppliers — when a supplier has different codes for different work types (e.g. Metro Security: installation vs removal vs keys), the pipeline matches invoice text against the work description to pick the correct code
- Added space-stripped matching so extracted names like "LampShopOnline" match "Lamp Shop Online"
- Warning shown on invoice cards when no nominal code mapping is found
- Added `.claude/settings.local.json` to `.gitignore`

## 2026-02-10 — Validation & Matching Improvements

- Allowed invoices over £200 to match with a warning instead of blocking
- Removed nominal code extraction and validation from the pipeline (now handled by mapping table)
- Added fuzzy match warning for invoices with missing PO numbers
- Removed VAT check validation
- Improved warning text layout with bullet icons
- Fixed header row detection in ExcelWriter that was matching title rows

## 2026-02-09 — V3 UI Overhaul

- Applied card board design with three-column layout (Matched / Review / Failed)
- Dark slate/navy palette with glassmorphism, grain texture, Outfit font
- Reset App button always visible, clears uploaded files
- Highlighted processed rows light blue in Excel output

## 2026-02-08 — Core Processing Engine

- Confirmation flow for near-miss invoices with improved error messages
- Overhauled extraction and matching for real-world invoices
- Consolidated documentation from 9 files to 3
- Removed CLI workflow, cleaned up project structure

## 2026-02-07 — Initial Release

- Invoice PDF extraction (generic + supplier-specific extractors)
- PO matching (exact, invoice number search, fuzzy multi-field)
- Excel reading/writing with dynamic header detection
- Streamlit web interface
