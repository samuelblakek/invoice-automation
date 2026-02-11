# Changelog

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
