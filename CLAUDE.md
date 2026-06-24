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
- `models/` — Data classes: `Invoice`, `PORecord`, `ValidationResult`
- `utils/` — Helpers (amount parsing, date parsing, string matching, supplier registry)
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
- **Multi-strategy PO matching** — Three strategies tried in order: exact PO match (cross-sheet via `find_po_record_any_sheet`), invoice number search, then fuzzy multi-field matching (store + amount + supplier). Fuzzy only runs for invoices with **no PO of their own** — a stated-but-missing PO reports "not found" rather than matching a different order. PO matching is exact-per-line, not substring (so `OT040` won't match `OT0402`).
- **Excel header detection** — Headers are at row 5-6, not row 0. The reader scans the first 20 rows for a cell whose value is exactly `PO` and uses that row as the header. A sheet that exists but fails to load is surfaced via `ExcelReader.load_warnings` (shown as a UI banner), since it would otherwise silently make every PO on it "not found".
- **Billing city exclusion** — When extracting store/delivery address, known billing HQ cities (e.g. "Dorking" for Menkind) and duplicate cities are excluded to find the actual delivery location.
- **Store name validation (allow-list)** — Every candidate from `_extract_store_location` is run through `_clean_town_or_empty`, which snaps it to a real Menkind store in `_KNOWN_STORES` (62 canonical names sourced from the Maintenance PO workbook — the data-sheet STORE columns + the two pivot tabs; "PB" rows excluded, typos normalised). It accepts an exact match or the longest known store name found as a contiguous word-run inside the candidate (longest-first, so "Glasgow Fort" / "Bluewater Upper" / "Meadowhall Lower" branches win over the bare town). `_STORE_ALIASES` resolves short forms (e.g. `Silverburn` → `Glasgow Silverburn`). No confident match returns `""` — never a street/address guess. The list lives in `data/known_stores.json` (loaded via `invoice_automation/utils/store_registry.py`, with the canonical names as defaults/fallback in that module). It's surfaced read-for-the-team in the sidebar "Store Names" editor, but **in-app edits do not persist** on Streamlit Cloud (ephemeral filesystem) — the UI says to contact Samuel. To make a durable add/correction, edit `data/known_stores.json` in the repo and push (or `DEFAULT_STORES` / `DEFAULT_ALIASES` in `store_registry.py`). Same ephemeral-persistence limitation as `data/nominal_codes.json`.
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
- **Supplier registry is the single source of truth** — `utils/supplier_registry.py` holds all supplier text/filename markers, names, and type codes. Both `GenericExtractor._identify_supplier()` and `web_app.identify_supplier()` delegate to it. To add a new supplier, add one entry there (plus a sheet mapping in `SheetSelector` and a nominal code row in the sidebar).
- **Supplier name mismatch** — The registry returns names like `"LampShopOnline"` or `"MetSafe"`, which may not match the mapping table's `"Lamp Shop Online"` or `"Metro Security (UK) Limited (MetSafe)"`. The lookup handles this via space-stripped comparison, but new suppliers may need entries in both the registry and the nominal code mapping.
- **Cost centre file removed** — The Cost Centre Summary uploader was removed. Nominal codes come from JSON, and `ExcelReader.cost_centre_path` is now optional (defaults to `None`).
- **ExcelReader caches sheet reads** — `_sheet_cache` prevents redundant disk I/O when the same sheet is accessed multiple times during matching. The cache lives for the lifetime of the `ExcelReader` instance.
- **Filename invoice-number fallback allows separators** — When no in-PDF pattern matches, `GenericExtractor._extract_invoice_number` derives the number from the filename. ILUX files are named `INV-10801.pdf` (hyphen), so the fallback regex is `INV([-_ ]?)(\d+)` — the separator is optional. A bare `INV(\d+)` silently returns nothing for hyphenated names and raises "Could not extract invoice number".
- **"Total ex VAT" is the NET line, not VAT** — The broad last-resort VAT pattern `\bVAT\b\s+£?(...)` will happily match `Total ex VAT £115.00` and report the net as the VAT. It carries a `(?<!ex )` lookbehind to prevent this. ILUX's current template puts the real VAT on a `Total Tax £23.00` line (older template used `Total VAT`); both patterns are present.
- **£ may render as `�` in the Windows terminal** — pdfplumber returns a real `£` (U+00A3); it just displays as the replacement glyph under the console code page. Check `ord()`/`repr()` before assuming an encoding problem — the amount regexes treat `£` as optional anyway.
- **File writes must set `encoding="utf-8"`** — on Windows `open(path, "w")` defaults to cp1252, which can't encode `✓`/`£`/other Unicode and raises `UnicodeEncodeError` mid-run. This crashed `save_detailed_report` (the `✓` pass symbol) and would silently differ for the CSV / nominal-codes JSON. The deployed app is on Linux (UTF-8 default) so it doesn't surface there, but always pass `encoding="utf-8"` on text reads/writes. Regression: `tests/test_report_generator.py`.
- **ILUX store is `Menkind - <Store>`, not the Site Address block** — ILUX's `Site Address:` section comes through column-merged and garbled (e.g. `Manchester [fTohrme uAltar...]`), so the old "last line of Site Address" logic grabbed the footer registration line. Store now comes from the `Menkind - <Store>` label (multi-word stores like `Milton Keynes` supported). This is step 0 in `_extract_store_location`.
- **ILUX `Order number` is `<ticket>/<PO>`** — e.g. `Order number 123118/OT0402` → PO is `OT0402` (after the slash); `123118` is the ticket no. Bare forms like `Order number LUX010` also occur. The `Order\s+number\s+(?:\d+/)?([A-Z]{2,4}\d{3,6})` pattern handles both.
- **ILUX POs span two sheets** — `OT…` codes live on the `OTHER` sheet, `LUX…` codes on the dedicated `ILUX` sheet. The supplier→sheet map (`SheetSelector`) routes ILUX to `OTHER`, but `POMatcher` Strategy 1 now uses `ExcelReader.find_po_record_any_sheet()` to fall back across all `MAINTENANCE_SHEETS` (which now includes `ILUX`) when the PO isn't in the mapped sheet. The supplier→sheet map is the starting point, not an exclusive filter.
- **Fuzzy matching (Strategy 3) only runs for PO-less invoices** — if an invoice states a PO that exact-match (Strategy 1, cross-sheet) and invoice-number (Strategy 2) both miss, `POMatcher` reports "PO '<x>' was not found in any maintenance sheet — not matched" rather than fuzzy-matching a *different* PO (which risked invoicing the wrong order). Genuinely PO-less invoices still use fuzzy store+supplier+amount scoring as before. The old "closest by store/amount" suggestion text was **removed** from failure messages (the user found it unhelpful — matching is direct-match only); the candidate scan still drives PO-less fuzzy matching, it just isn't surfaced as a hint.
- **Extractors are intentionally NOT cached** — `web_app.get_extractors()` must not be wrapped in `@st.cache_resource`: the cache served stale extractor instances after a redeploy (code changes didn't take effect until a manual reboot). The extractors are cheap to build and `BaseExtractor` caches compiled regexes at class level, so there's no benefit to caching the instances.
- **Access password gate** — `web_app._check_password()` gates the whole app behind a shared password read from `st.secrets["app_password"]` (set it in Streamlit Cloud → Settings → Secrets). If the secret is absent the app is open (local dev). It's a shared-secret gate, not per-user identity; `st.login` (OIDC) is the upgrade path. `.streamlit/secrets.toml` is gitignored; see `.streamlit/secrets.toml.example`.
- **Model invariants live in the dataclasses** — `Invoice.__post_init__` requires a non-blank `invoice_number` and coerces money fields to `Decimal`; use `Invoice.has_po` / `has_store` (not raw truthiness — a real £0 is falsy). `ValidationResult.is_valid` / `can_auto_update` / `errors` / `warnings` are derived `@property`s (don't set them; `finalize()` is a no-op kept for compatibility). Amount fields stay `Decimal` with `0` meaning zero/unread — compare with `> 0`, never truthiness.

## UI / Styling

- **Design system is the source of truth**: `design-system/SPEC.md` defines every token (colour, spacing, radius, shadow, typography, motion, focus); `design-system/REVIEW.md` is the audit + QA checklist. `GLOBAL_CSS` is **fully tokenised** — every value references a `:root` token; the only raw values allowed outside `:root` are `0` and the grain-overlay SVG. When adding CSS, add a token rather than hardcoding, and keep it AA-compliant.
- **Layout**: three-column card board (Matched / Review / Failed) with sidebar file uploaders
- **Font**: Outfit (Google Fonts) -- single family for headings + body
- **Palette**: Dark slate/navy (#0F1923 bg) with glassmorphism (rgba + backdrop-blur) cards
- **Texture**: Layered radial gradients with subtle blue/purple colour glow, SVG noise/grain overlay, frosted glass cards + sidebar
- **Accessibility (WCAG 2.2 AA)**: muted text is `#7C8BA1` (not `#64748B`, which failed contrast); `:focus-visible` rings (`--ring #38BDF8`) on all interactive elements; `:active`/`:disabled` states; 44px touch targets; `prefers-reduced-motion` block. Don't regress these.
- **Cards**: `.inv-card` has a **thin 1px low-contrast left accent** (muted `--green-border` / `--red-border` token) — not the old 3px saturated stripe. Warnings and errors render as compact **`.inv-note` callouts** (calm `--text-secondary` body text, status carried only by the ⚠ icon colour, thin top divider) built by `inv_note_html()`. A blank store shows a `.inv-store-unknown` "Store: Unknown ⚠" alert (informational — never fails a PO-matched invoice).
- **Message tone**: validation messages are plain English (no `store='X'` code syntax, no "closest/similar PO" suggestions).
- **CSS**: All styling in the GLOBAL_CSS constant at the top of web_app.py, injected via st.markdown() -- uses ::after pseudo-element on .stApp for the noise overlay (pointer-events: none)
- **Streamlit theme**: .streamlit/config.toml must stay in sync with CSS colour tokens
- **Icon fonts**: Material Symbols Rounded used by Streamlit for expander/sidebar icons -- font override rules must preserve these (see CSS comments)

## Lessons

See `tasks/lessons.md` for accumulated patterns and corrections from development.
