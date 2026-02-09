# User Guide

## Web App Workflow

### Step 1: Prepare Your Files

1. Export invoices from iCompleat as PDFs
2. Download the latest Maintenance PO spreadsheet and Cost Centre Summary from your network drive

### Step 2: Upload Files

1. Open the web app URL in your browser (Chrome recommended)
2. Upload invoice PDFs — drag and drop or click "Browse files" (you can select multiple at once)
3. Upload the Maintenance PO spreadsheet (.xlsx)
4. Upload the Cost Centre Summary (.xlsx)

### Step 3: Process

1. Click "Process Invoices" (button turns blue when all files are uploaded)
2. Wait for "Processing Complete" — don't close the browser or refresh the page

### Step 4: Review Results

The summary shows:
- **Auto-Updated** — successfully processed and written to Excel
- **Needs Review** — flagged for manual attention (see issues column)
- **Failed** — couldn't process (see detailed report)

### Step 5: Download

Click "Download Updated Excel" — this is your updated Maintenance PO spreadsheet. Save it to your network drive.

Optional downloads:
- **CSV Summary** — spreadsheet summary for record-keeping
- **Detailed Report** — text file explaining each validation decision

### Step 6: Finish Up (Manual Steps)

The automation cannot do these:
1. Save the updated Excel to your network drive
2. Approve invoices in iCompleat
3. Highlight completed rows grey (optional)

---

## CLI Workflow

For advanced users who prefer the command line.

### Setup

```bash
pip install -r requirements.txt
```

Configure file paths in `config.yaml`:

```yaml
paths:
  maintenance_workbook: "/path/to/Maintenance POs.xlsx"
  cost_centre_summary: "/path/to/Cost Centre Summary.xlsx"
  invoices_input_dir: "./invoices_to_process"
  output_dir: "./output"
```

### Process Invoices

```bash
# Copy PDFs into invoices_to_process/
python main.py process --input-dir ./invoices_to_process

# Preview only (no Excel changes)
python main.py process --input-dir ./invoices_to_process --dry-run
```

### Check Results

Reports are saved to `output/`:
- `invoice_summary_YYYYMMDD.csv` — open in Excel
- `invoice_report_YYYYMMDD.txt` — detailed text report

### Clean Up

Delete or move processed PDFs from `invoices_to_process/` after each run.

---

## What Gets Updated

Only 3 columns in matching PO rows:

| Column | Updated To |
|--------|------------|
| INVOICE NO. | Invoice number from the PDF |
| INVOICE AMOUNT (EX VAT) | Net amount excluding VAT |
| INVOICE SIGNED | Today's date |

Everything else in the spreadsheet is preserved: formulas, formatting, conditional formatting, other columns, other sheets.

---

## Validation Checks

Every invoice goes through these checks. All must pass for auto-update:

1. **PO exists** — the PO number is found in the correct Excel sheet
2. **Not already invoiced** — the PO row doesn't already have an invoice number
3. **Store matches** — the store name on the invoice matches the PO (fuzzy matching, 70% threshold)
4. **Nominal code correct** — cost code matches
5. **£200+ authorization** — if the net amount exceeds £200, both "QUOTE OVER £200" and "AUTHORISED" columns must have values. Auto-update is **blocked** if authorization is missing.
6. **Amount valid** — net amount is positive

---

## Common Issues and Fixes

### "PO number not found"
The PO doesn't exist in the spreadsheet. Add it manually, or process this invoice by hand.

### "PO already invoiced"
This PO row already has an invoice number. Check if it's a duplicate or a different invoice for the same PO.

### "Quote authorization missing" (over £200)
The invoice exceeds £200 but the quote isn't authorized in the spreadsheet. Get authorization, fill in the AUTHORISED column, and reprocess.

### "Store name doesn't match"
The invoice shows a different store name than the PO. This is usually safe to update manually — the fuzzy matching is being cautious.

### Wrong amount displayed
The automation extracts **net** (ex-VAT) amounts. If the amount looks wrong, check the PDF — look for "Net Total" or "Sub Total", not the total including VAT.

---

## Troubleshooting

### Web app won't load
- Refresh the page (F5)
- Try a different browser
- Check your internet connection

### Upload fails
- Close the file in Excel first
- Ensure it's .xlsx format (not .xls or .csv)
- File size must be under 200MB

### Processing stuck
- Large batches take longer — wait for completion
- If stuck for more than 5 minutes, refresh and try again
- Process smaller batches (10-20 invoices at a time)

### Downloaded Excel won't open
- Check your Downloads folder for the file
- On Windows: right-click the file -> Properties -> Unblock
- Try opening directly from Excel (File -> Open) rather than double-clicking

---

## Tips

- **Process in batches** of 10-20 invoices rather than waiting for 50+
- **Always use the latest Excel files** from your network drive, not last week's copies
- **Don't close the browser** while processing
- **Check the summary numbers** before downloading — if Auto-Updated equals Total, everything worked

---

## Weekly Checklist

```
Pre-Processing:
[ ] Downloaded latest Excel files from network drive
[ ] Exported invoices from iCompleat as PDFs

Processing:
[ ] Uploaded invoice PDFs
[ ] Uploaded Maintenance PO spreadsheet
[ ] Uploaded Cost Centre Summary
[ ] Clicked "Process Invoices"
[ ] Waited for "Processing Complete"

Review:
[ ] Checked summary numbers
[ ] Reviewed any flagged invoices
[ ] Downloaded updated Excel file
[ ] Saved updated Excel to network drive

Post-Processing:
[ ] Fixed flagged invoices manually (if any)
[ ] Approved invoices in iCompleat
```
