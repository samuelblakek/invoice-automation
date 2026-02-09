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
