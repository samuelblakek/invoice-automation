# Lessons Learned

## 1. Don't write supplier-specific logic — keep extraction generic

**Trigger:** User corrected me for adding `if 'lampshoponline' in text.lower()` checks in store extraction.

**Rule:** Extraction patterns must work based on *what appears on invoices* (field labels, address formats, city+postcode patterns), not *who the supplier is*. If a pattern fails for a specific invoice, the fix should be a more general pattern that handles the underlying text structure, not a supplier-name check.

**Example:** Instead of `if 'lampshoponline' in text: use_special_logic()`, find the actual text pattern that distinguishes billing vs delivery addresses (e.g. "Dorking" is always the billing HQ, duplicated city names are likely supplier addresses).

## 2. City+Postcode extraction — exclude known billing addresses, not supplier names

**Pattern:** Menkind's HQ is always "Dorking, RH4 1XA". When multiple City+Postcode pairs appear, exclude Dorking (billing) and cities that appear more than once (likely supplier's registered address). The remaining city is the delivery/store location.

## 3. pdfplumber merges columns into single lines

**Pattern:** When a PDF has multi-column layouts (Customer Address | Delivery Address | Our Address), pdfplumber merges them into single lines. Don't assume addresses are on separate lines — look for patterns within merged lines.

## 4. VAT extraction must require decimal format

**Pattern:** `VAT\s+£?\s*(\d+)` is too broad — it matches dates (14/01/2026) and line items. Always require `\.\d{2}` at the end to match currency amounts specifically.

## 5. Excel sheets have title/legend rows before headers

**Pattern:** The Maintenance PO workbook has 4-5 rows of title/color-legend before the actual header row (PO, STORE, etc.). Always scan for the header row dynamically — never assume row 0 is the header.

## 6. PO cells can contain embedded whitespace/newlines

**Pattern:** CJL sheet has PO values like `\nCJL408\n`. Use substring/contains matching, not exact comparison. Strip and normalize before matching.

## 7. Centralise supplier identification in a single registry

**Trigger:** Tech debt scan found supplier identification logic triplicated across GenericExtractor, web_app.py, and extractors.

**Rule:** `utils/supplier_registry.py` is the single source of truth for mapping text/filename markers to supplier names and type codes. Both extractors and the web app delegate to `identify_supplier()` from the registry. To add a new supplier, add one entry there.

## 8. Never monkey-patch dataclass fields — add them properly

**Trigger:** `result._nominal_code = nom_code` was used to attach nominal codes to ValidationResult at runtime, then retrieved with `getattr(result, "_nominal_code", "")`.

**Rule:** If a dataclass needs a new field, add it with a default value. Monkey-patching bypasses type checking, breaks IDE support, and makes the code fragile.

## 9. Verify dead code is truly dead before deleting

**Trigger:** Deleted 370+ lines of unused methods from utility classes.

**Rule:** Before deleting any method, grep the entire codebase for references (not just the definition). A method is safe to remove only if zero call sites exist outside its own definition. After deletion, verify all imports still work.
