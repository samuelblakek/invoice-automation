# Invoice Amount Extraction Fixes

## Issue
Invoice amounts were not being correctly extracted as NET (ex-VAT) values. Some extractors were picking up totals that included VAT or failing to find amounts at all.

## Fixes Applied

### 1. APS Extractor (`aps_extractor.py`)
**Problem**: Showing £0.00 instead of £573.00
- **Root Cause**: Pattern `(?:Sub Total|Net)` didn't match APS format "NET TOTAL £ 573.00"
- **Fix**: Added specific pattern for "NET TOTAL £ XXX.XX" format
- **Result**: ✓ Now extracts £573.00 correctly

```python
# Before: Generic pattern missed "NET TOTAL"
net_amount = self._find_pattern(text, r'(?:Sub Total|Net)\s*:?\s*£?\s*([\d,]+\.?\d*)', ...)

# After: Specific pattern for APS format
net_match = re.search(r'NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
```

### 2. Compco Extractor (`generic_extractor.py`)
**Problem**: Showing £1.00 instead of £95.00
- **Root Cause**: Pattern didn't match Compco's "NET 95.00" format in VAT Analysis section
- **Fix**: Added pattern to find "NET" amount after "VAT Analysis" section
- **Result**: ✓ Now extracts £95.00 correctly

```python
# Added Compco-specific pattern
r'VAT Analysis.*?NET\s+([\d,]+\.?\d*)',
```

### 3. Amazon Extractor (`amazon_extractor.py`)
**Problem**: Showing £19.97 instead of exact £19.96
- **Root Cause**: Calculating from total (23.96 / 1.20) instead of reading actual breakdown
- **Fix**: Modified to read page 2 which has itemized breakdown "Total £19.96 £4.00"
- **Result**: ✓ Now extracts exact £19.96 from breakdown table

```python
# Before: Only looked at page 1 "Total payable"
# After: Reads page 2 breakdown table
match = re.search(r'Total\s+£([\d,]+\.?\d*)\s+£([\d,]+\.?\d*)', text)
if match:
    net_amount = parse_amount(match.group(1))  # First number is NET
    vat_amount = parse_amount(match.group(2))  # Second is VAT
```

### 4. AAW Extractor (`aaw_extractor.py`)
**Status**: Already correct (£116.50)
- No changes needed - pattern worked correctly

### 5. CJL Extractor (`cjl_extractor.py`)
**Status**: Already correct (£518.00)
- No changes needed - "Sub Total" pattern worked correctly

## Additional Fixes

### Invoice Number Extraction
- **Amazon**: Fixed to extract "GB5Q1QGABEY" (was picking up "date")
- **Compco**: Fixed to extract "0000031483" from "Ref" field (was picking up "CLEEVE")

### PO Number Extraction
- **Compco**: Fixed to extract "ER22/10808" from "Order No./Job" field (was getting "/Job")

### Store Name Extraction
- **Compco**: Fixed to extract "UNIT 104 BRAEHEAD CENTRE" (was getting metadata tags)

## Verification Results

| Supplier | Invoice # | Net Amount | Previous | Status |
|----------|-----------|------------|----------|---------|
| AAW | 5002746 | **£116.50** | £116.50 | ✓ Correct |
| CJL | 28564 | **£518.00** | £518.00 | ✓ Correct |
| APS | 24443 | **£573.00** | ~~£0.00~~ | ✓ FIXED |
| Amazon | GB5Q1QGABEY | **£19.96** | ~~£19.97~~ | ✓ FIXED |
| Compco | 0000031483 | **£95.00** | ~~£1.00~~ | ✓ FIXED |

## Key Principles Applied

### 1. NET Amount Priority
Always extract NET (ex-VAT) amounts, never totals that include VAT unless calculating:
```python
# Good: Explicit NET pattern
r'NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)'
r'Sub Total\s+([\d,]+\.?\d*)'

# Bad: Ambiguous "Total" (could include VAT)
r'Total\s+£([\d,]+\.?\d*)'  # ✗ Might be total WITH VAT
```

### 2. Supplier-Specific Patterns
Each supplier has unique invoice formats requiring tailored patterns:
- **AAW**: "Total" (before VAT line) = NET
- **CJL**: "Sub Total" = NET
- **APS**: "NET TOTAL" = NET
- **Amazon**: Page 2 breakdown table = NET
- **Compco**: "VAT Analysis" section "NET" = NET

### 3. Multi-Page Support
Some invoices (like Amazon) require reading multiple pages:
```python
text = self._extract_text(pdf_path)  # Gets ALL pages
```

### 4. Pattern Specificity Order
Try most specific patterns first, fallback to generic:
```python
# Try specific pattern first
net_match = re.search(r'NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)', text)
if net_match:
    net_amount = parse_amount(net_match.group(1))
# Fallback to generic
if not net_amount:
    net_amount = parse_amount(self._find_pattern(text, r'(?:Sub Total|Net)...'))
```

## Testing

All extractors verified with actual invoice PDFs:
```bash
python main.py process --input-dir example-files --dry-run
```

Results show all NET amounts correctly extracted and reported in CSV output.

## Critical for Production

**ALWAYS verify NET amounts are ex-VAT:**
1. Check CSV output: `output/invoice_summary_YYYYMMDD.csv`
2. Compare against physical invoices
3. NET should never equal "Total payable" unless VAT is £0.00

## Future Improvements

1. **Add validation**: Compare extracted NET + VAT against total
2. **Multi-currency support**: Currently assumes GBP (£)
3. **OCR fallback**: For scanned PDFs without text layer
4. **Pattern learning**: Machine learning to detect new formats automatically
