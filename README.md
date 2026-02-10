# Invoice Processing Automation

Automated invoice processing for retail operations. Extracts data from supplier PDF invoices, validates against Purchase Orders in Excel, enforces the company's £200+ quote authorization policy, and auto-updates the Maintenance PO spreadsheet — preserving all formatting and formulas.

No AI or LLM tokens are used at runtime. The app is entirely rule-based: regex pattern matching, fuzzy string comparison (Levenshtein distance), and pandas lookups.

## How to Run

```bash
pip install -r requirements.txt
streamlit run web_app.py
```

The web app opens at `http://localhost:8501`. Upload invoice PDFs and the two Excel files (Maintenance POs + Cost Centre Summary), click Process, and download the updated spreadsheet.

## How It Works

```
PDF invoices
  -> pdfplumber extracts text
  -> Regex patterns extract: invoice #, PO #, net amount (ex-VAT), store, supplier
  -> pandas searches Excel for matching PO record
  -> Validation: PO exists, not already invoiced, store matches, £200+ authorized
  -> openpyxl updates 3 columns: INVOICE NO., INVOICE AMOUNT (EX VAT), INVOICE SIGNED
  -> Download updated Excel + CSV summary + detailed report
```

All processing happens in memory. No files are stored on disk or on the server.

## Project Structure

```
retail-support-automate-invoices/
├── web_app.py                    # Streamlit web interface (entry point)
├── requirements.txt              # Python dependencies
├── invoice_automation/           # Core package
│   ├── extractors/               # PDF data extraction
│   │   ├── generic_extractor.py  # Multi-pattern extractor (handles any supplier)
│   │   ├── aaw_extractor.py      # AAW-specific extractor
│   │   ├── cjl_extractor.py      # CJL-specific extractor
│   │   ├── aps_extractor.py      # APS-specific extractor
│   │   ├── amazon_extractor.py   # Amazon-specific extractor
│   │   └── base_extractor.py     # Abstract base class
│   ├── processors/               # Excel reading/writing, sheet selection
│   ├── validators/               # PO matching, authorization checks
│   ├── models/                   # Data classes (InvoiceData, PORecord)
│   ├── utils/                    # Amount parsing, text normalization
│   └── reports/                  # CSV and text report generation
├── example-files/                # Test PDFs and Excel files
├── docs/                         # Documentation
│   ├── deployment.md             # Deployment & hosting guide
│   └── user-guide.md             # End-user workflow guide
└── tasks/                        # Development tracking
    ├── todo.md                   # Current task status
    └── lessons.md                # Patterns learned during development
```

## Tech Stack

| Library | Purpose |
|---------|---------|
| **pdfplumber** | PDF text extraction |
| **pandas** | Excel data processing, fast PO lookups |
| **openpyxl** | Excel cell updates (preserves formatting/formulas) |
| **fuzzywuzzy** | Store name fuzzy matching (Levenshtein distance) |
| **Streamlit** | Web interface |

## Documentation

- [Deployment Guide](docs/deployment.md) — Streamlit Cloud setup, local testing, alternative hosting, security
- [User Guide](docs/user-guide.md) — Web app workflow, validation checks, troubleshooting

## License

Private use only. Not for distribution.
