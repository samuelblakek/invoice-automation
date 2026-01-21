# How the App Actually Works

This document explains the technical workings of the Invoice Processing Automation system.

## Key Point: No AI/Claude Tokens Used

**This app does NOT use Claude, OpenAI, or any AI/LLM to process invoices.** It is entirely rule-based traditional programming. Claude Code was used to *write* the code, but the running application uses zero AI tokens.

---

## Technology Stack

| Component | Purpose | How It Works |
|-----------|---------|--------------|
| **pdfplumber** | PDF text extraction | Parses PDF file structure to extract raw text |
| **Regex patterns** | Data extraction | Pattern matching (e.g., `Invoice No: (\d+)`) |
| **pandas** | Excel data processing | DataFrame operations for fast lookups |
| **openpyxl** | Excel file updates | Direct cell manipulation preserving formatting |
| **fuzzywuzzy** | Store name matching | Levenshtein distance algorithm (not AI) |
| **Streamlit** | Web interface | Python web framework for the UI |

---

## Processing Flow

```
┌─────────────────┐
│   PDF Invoice   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  pdfplumber extracts raw text       │
│  (parses PDF structure, no AI)      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Supplier identification            │
│  (filename + text pattern matching) │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Regex patterns extract:            │
│  - Invoice number                   │
│  - PO number                        │
│  - NET amount (ex-VAT)              │
│  - Store location                   │
│  - Invoice date                     │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  pandas searches Excel for          │
│  matching PO record (vectorized)    │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Rule-based validation:             │
│  - PO exists? (if/else)             │
│  - Store matches? (fuzzy matching)  │
│  - £200+ authorized? (if/else)      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  openpyxl updates Excel cells       │
│  (preserves formulas & formatting)  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Updated Excel  │
│  + CSV Report   │
└─────────────────┘
```

---

## Example: How Data Extraction Works

### Invoice Number Extraction (AAW invoices)

```python
# Pure regex pattern matching - no AI involved
match = re.search(r'Invoice\s+No[:\s]+(\d+)', text, re.IGNORECASE)
if match:
    invoice_number = match.group(1)  # e.g., "5002746"
```

### NET Amount Extraction (APS invoices)

```python
# Looks for literal text "NET TOTAL £" followed by numbers
net_match = re.search(r'NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
if net_match:
    net_amount = Decimal(net_match.group(1))  # e.g., Decimal("573.00")
```

### Store Name Matching

```python
# Uses Levenshtein distance algorithm (edit distance), not AI
from fuzzywuzzy import fuzz

similarity = fuzz.ratio("Maidstone", "MAIDSTONE")  # Returns 100
similarity = fuzz.ratio("Maidston", "MAIDSTONE")   # Returns 94

if similarity >= 70:  # 70% threshold
    match_found = True
```

---

## Supplier-Specific Extractors

Each supplier has different invoice formats, so we have dedicated extractors:

| Supplier | Extractor | Key Patterns |
|----------|-----------|--------------|
| AAW National | `aaw_extractor.py` | "Invoice No", "Order No PS...", "Total £" |
| CJL Group | `cjl_extractor.py` | "Invoice Number:", "Your Order No:", "Net Value" |
| APS Fire | `aps_extractor.py` | "NO.", "P/O", "NET TOTAL £" |
| Amazon | `amazon_extractor.py` | Multi-page, reads breakdown table on page 2 |
| Compco | `generic_extractor.py` | "VAT Analysis" section for NET amount |

---

## Validation Logic

All validation is simple if/else logic:

### £200+ Quote Authorization Check

```python
if invoice.net_amount > Decimal("200.00"):
    # Check if quote reference exists
    if not po_record.quote_over_200:
        return "BLOCKED: No quote reference for invoice over £200"

    # Check if authorization exists
    if not po_record.authorized:
        return "BLOCKED: Quote not authorized"

    return "PASSED"
else:
    return "PASSED"  # No authorization needed under £200
```

### PO Matching

```python
# Simple string comparison
if extracted_po_number == excel_po_number:
    return "Match found"
else:
    return "PO not found"
```

---

## What Powers the Deployed App

| Resource | Provider | Cost |
|----------|----------|------|
| Web hosting | Streamlit Cloud | **Free** |
| Python execution | Streamlit Cloud servers | **Free** |
| PDF processing | pdfplumber library | **Free** |
| Excel processing | pandas + openpyxl | **Free** |

### What is NOT used:

- Claude API tokens
- OpenAI API
- Any AI/ML inference
- Any paid APIs
- Any cloud AI services

---

## Performance Optimizations

The app includes several optimizations for speed:

1. **Cached extractors** - Extractor instances are created once and reused
2. **Compiled regex cache** - Regex patterns compiled once, not per-use
3. **Vectorized pandas operations** - Fast PO lookups instead of row iteration
4. **In-memory processing** - No temporary files written to disk

---

## Data Privacy

- **No data sent to AI services** - All processing happens on Streamlit's servers
- **No data storage** - Files are processed in memory and discarded
- **No logging of invoice data** - Only error messages logged
- **HTTPS encryption** - All uploads/downloads encrypted in transit

---

## Summary

| Question | Answer |
|----------|--------|
| Does this use AI to read PDFs? | **No** - uses pdfplumber (text parsing) |
| Does this use AI to extract data? | **No** - uses regex pattern matching |
| Does this use Claude tokens? | **No** - zero AI tokens used |
| What's the ongoing cost? | **£0** - entirely free |
| Is it deterministic? | **Yes** - same input = same output every time |
| Where does processing happen? | Streamlit Cloud servers (free tier) |

---

## Technical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER'S BROWSER                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Streamlit Web Interface                    │   │
│  │  - File upload (drag & drop)                        │   │
│  │  - Process button                                    │   │
│  │  - Results display                                   │   │
│  │  - Download buttons                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 STREAMLIT CLOUD (Free Tier)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    web_app.py                        │   │
│  │                        │                             │   │
│  │    ┌───────────────────┼───────────────────┐        │   │
│  │    ▼                   ▼                   ▼        │   │
│  │ ┌──────────┐    ┌────────────┐    ┌────────────┐   │   │
│  │ │pdfplumber│    │   pandas   │    │  openpyxl  │   │   │
│  │ │(PDF read)│    │(Excel read)│    │(Excel write│   │   │
│  │ └──────────┘    └────────────┘    └────────────┘   │   │
│  │       │                │                 │          │   │
│  │       ▼                ▼                 ▼          │   │
│  │ ┌──────────────────────────────────────────────┐   │   │
│  │ │              Python Processing               │   │   │
│  │ │  - Regex pattern matching                    │   │   │
│  │ │  - Rule-based validation                     │   │   │
│  │ │  - Fuzzy string matching                     │   │   │
│  │ │  - Data transformation                       │   │   │
│  │ └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NO CONNECTION TO:                                          │
│  ✗ Claude API                                               │
│  ✗ OpenAI API                                               │
│  ✗ Any AI/ML services                                       │
│  ✗ Any paid APIs                                            │
└─────────────────────────────────────────────────────────────┘
```

---

*This document was created to clarify that the Invoice Processing Automation system is a traditional rule-based application with no AI/ML components or token usage.*
