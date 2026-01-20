# Invoice Automation - Weekly User Guide

## How to Process Your Invoices Each Week

This is what you'll do **every week** to process your invoices. It's simple - just 5 steps!

---

## 🎯 Quick Start (The Short Version)

1. Export invoices from iCompleat → Save PDFs to `invoices_to_process` folder
2. Double-click `RUN_AUTOMATION` script
3. Wait 30 seconds (it shows you what it's doing)
4. Check the summary report
5. Open Excel and approve invoices in iCompleat

**That's it!** The automation handles all the data entry for you.

---

## 📋 Detailed Steps (With Pictures)

### Step 1: Export Invoices from iCompleat

1. Log into iCompleat (you already know how to do this)
2. Export your invoices as PDFs (your usual process)
3. Save all the PDFs somewhere on your computer

**Time**: 5 minutes

---

### Step 2: Put PDFs in the Right Folder

1. Open the `retail-support-automate-invoices` folder
2. Open the `invoices_to_process` folder (it's empty at first)
3. **Copy all your invoice PDFs** into this folder
4. You should see files like:
   - AAW invoice 12345.pdf
   - CJL Invoice 67890.pdf
   - Amazon Invoice ABC123.pdf

**Time**: 1 minute

---

### Step 3: Run the Automation

#### On Windows:
1. Go back to the main `retail-support-automate-invoices` folder
2. **Double-click** the file `RUN_AUTOMATION.bat`
3. A window will open showing you what's happening

#### On Mac:
1. Go back to the main `retail-support-automate-invoices` folder
2. **Double-click** the file `RUN_AUTOMATION.command`
3. A terminal window will open showing you what's happening

**What you'll see**:
```
Invoice Processing Automation
============================================================
Found 10 invoice(s)

Processing: AAW invoice 5002746.pdf
  Supplier: AAW National Shutters Ltd
  Invoice #: 5002746
  PO #: PS0301111817
  Amount: £116.50
  Status: ✓ PASSED - Ready for auto-update

Processing: CJL Invoice 28564.pdf
  ...
```

The window will show:
- ✓ Green checkmarks = Auto-updated successfully
- ✗ Red crosses = Needs manual review (see why below it)

**Time**: 30 seconds to 2 minutes (depending on how many invoices)

---

### Step 4: Check the Reports

When the automation finishes, you'll see:

```
============================================================
Invoice Processing Summary
============================================================
Total Invoices Processed: 10
Auto-Updated Successfully: 8
Flagged for Manual Review: 2
Failed to Process: 0
============================================================
```

#### Where to Find the Reports:

1. Open the `output` folder (inside `retail-support-automate-invoices`)
2. You'll see two new files:
   - `invoice_summary_20260120.csv` (spreadsheet you can open in Excel)
   - `invoice_report_20260120.txt` (detailed text report)

#### Understanding the Reports:

**invoice_summary_YYYYMMDD.csv** (Open in Excel):
| Status | Invoice Number | Supplier | PO Number | Store | Amount | Errors |
|--------|----------------|----------|-----------|-------|--------|--------|
| SUCCESS | 5002746 | AAW | PS0301111817 | Maidstone | £116.50 | |
| ERROR | 28564 | CJL | CJL316 | Portsmouth | £518.00 | PO not found |

- **SUCCESS** = Auto-updated ✓
- **ERROR** = Needs your attention ✗

**invoice_report_YYYYMMDD.txt** (Open in Notepad/TextEdit):
- Shows exactly what was checked for each invoice
- Tells you WHY an invoice failed (if it did)
- Use this to fix problems

**Time**: 2 minutes to review

---

### Step 5: Handle Invoices That Need Manual Review

Some invoices might not auto-update. Common reasons:

#### 1. PO Number Not Found
**Why**: The PO doesn't exist in your spreadsheet yet
**Fix**:
- Add the PO to the spreadsheet manually
- Run the automation again

#### 2. PO Already Invoiced
**Why**: This PO already has an invoice number
**Fix**:
- Check if it's a duplicate
- If it's a different invoice, update manually

#### 3. Quote Not Authorized (Over £200)
**Why**: Invoice is over £200 but quote isn't authorized
**Fix**:
- Get the quote authorized
- Fill in the "AUTHORISED" column
- Run automation again

#### 4. Store Name Doesn't Match
**Why**: Invoice shows "Leicester" but PO shows "Leicester - Highcross"
**Fix**:
- Usually safe to update manually
- The fuzzy matching is just being cautious

**Time**: 5-10 minutes (only for invoices that failed)

---

### Step 6: Final Manual Steps (iCompleat)

The automation **CAN'T** do these steps (they're in iCompleat):

1. **Approve invoices in iCompleat** (your usual process)
2. **Highlight completed rows grey** in Excel (optional - future enhancement)

**Time**: 5 minutes

---

### Step 7: Clean Up for Next Week

1. **Delete** or **move** the PDF files from `invoices_to_process` folder
2. They've been processed, so you don't need them there anymore
3. Keep your `invoices_to_process` folder empty until next week

**Time**: 30 seconds

---

## 🎨 Visual Summary

```
Week 1:
┌─────────────────────────────────┐
│ 1. Export from iCompleat        │
│    ↓                             │
│ 2. Copy PDFs to folder           │
│    ↓                             │
│ 3. Double-click RUN_AUTOMATION   │
│    ↓                             │
│ 4. Review reports                │
│    ↓                             │
│ 5. Fix any errors (if needed)    │
│    ↓                             │
│ 6. Approve in iCompleat          │
│    ↓                             │
│ 7. Delete processed PDFs         │
└─────────────────────────────────┘
```

---

## ⚙️ Advanced Options (Optional)

### Dry Run Mode (Preview Without Changes)

Want to see what will happen **without** updating Excel?

1. Open the `RUN_AUTOMATION` file (right-click → Edit)
2. You'll see: `python main.py process --input-dir ./invoices_to_process`
3. Change it to: `python main.py process --input-dir ./invoices_to_process --dry-run`
4. Save and close
5. Now when you run it, it shows you what **would** happen but doesn't update Excel

**When to use**:
- Testing with new invoice formats
- Want to check before making changes
- Nervous about auto-updates

Remember to **remove** `--dry-run` when you want it to update Excel again!

---

## 📊 What Gets Updated in Excel

The automation updates these 3 columns in your Maintenance PO spreadsheet:

| Column | What It Updates |
|--------|-----------------|
| INVOICE NO. | The invoice number from the PDF |
| INVOICE AMOUNT (EX VAT) | The net amount (excluding VAT) |
| INVOICE SIGNED | Today's date |

**What it DOESN'T touch**:
- Everything else in the spreadsheet
- Formulas are preserved
- Formatting is preserved
- Only updates rows where PO matches

---

## 🔍 Checking It Worked

### Quick Check:
1. Open your Maintenance PO Excel file
2. Look for the PO numbers from your invoices
3. Those rows should now have:
   - Invoice number filled in
   - Invoice amount filled in
   - Invoice signed date filled in

### Detailed Check:
1. Compare the CSV summary report with Excel
2. Invoice numbers should match
3. Amounts should match (ex-VAT amounts)
4. Dates should be today

---

## ⚠️ Common Mistakes to Avoid

1. **❌ Running automation while Excel is open**
   - Close Excel first!
   - The automation needs to write to the file

2. **❌ Wrong file paths in config.yaml**
   - Make sure paths point to YOUR files
   - Use forward slashes `/` not backslashes `\`

3. **❌ PDFs in wrong folder**
   - Must be in `invoices_to_process` folder
   - Not in subfolders

4. **❌ Expecting it to approve invoices**
   - It only updates the spreadsheet
   - You still need to approve in iCompleat

5. **❌ Not reviewing the reports**
   - Always check the summary!
   - Don't assume everything worked

---

## 💡 Tips & Tricks

### Tip 1: Process in Batches
- Don't wait until you have 100 invoices
- Process 10-20 at a time
- Easier to spot errors

### Tip 2: Keep a Backup
- The automation creates backups automatically
- They're named: `Maintenance POs.backup.xlsx`
- Don't delete these until you're sure updates are correct

### Tip 3: Check the Output Folder Regularly
- Old reports pile up
- Delete reports older than a month
- Keeps things tidy

### Tip 4: Name Your PDFs Clearly
- Keep supplier name in filename
- Examples: "AAW invoice 12345.pdf", "CJL Invoice 67890.pdf"
- Helps the automation identify the supplier

---

## 🆘 When Something Goes Wrong

### Error: "No PDFs found"
**Fix**: Make sure PDFs are in `invoices_to_process` folder

### Error: "Excel file is locked"
**Fix**: Close the Excel file

### Error: "Config file not found"
**Fix**: Make sure `config.yaml` exists in the main folder

### Error: "All invoices failed"
**Fix**: Check your Excel file paths in `config.yaml`

### Error: Wrong amounts
**Fix**: The automation extracts NET amounts (ex-VAT). If amounts look wrong, check the PDF to confirm.

---

## 📞 Getting Help

If something isn't working:

1. **Don't panic!** The automation creates backups
2. Check the detailed report in `output/invoice_report_YYYYMMDD.txt`
3. Take screenshots of any error messages
4. Contact IT or the person who set this up

---

## 🎓 Understanding the Validation Checks

The automation checks these things for EVERY invoice:

### ✓ PO Exists
- Searches for the PO number in the correct Excel sheet
- **Fails if**: PO not found

### ✓ PO Not Already Invoiced
- Checks if the PO already has an invoice number
- **Fails if**: Duplicate invoice

### ✓ Store Matches
- Compares invoice store with PO store
- Uses "fuzzy matching" (allows small differences)
- **Fails if**: Names are completely different

### ✓ £200+ Authorization Check ⚠️ IMPORTANT
- If invoice is over £200 (ex-VAT):
  - Checks "QUOTE OVER £200" column has a value
  - Checks "AUTHORISED" column has a value
- **Fails if**: Quote not authorized

### ✓ Amount Valid
- Checks amount is positive
- Checks VAT calculation is correct
- **Fails if**: Amount is negative or zero

**All checks must pass** for auto-update. If any fail, it flags for manual review.

---

## 🏁 Summary: Your Weekly Workflow

1. ✅ Export invoices → `invoices_to_process` folder (5 min)
2. ✅ Double-click `RUN_AUTOMATION` (1 min)
3. ✅ Review reports (2 min)
4. ✅ Fix any flagged invoices (5-10 min if needed)
5. ✅ Approve in iCompleat (5 min)
6. ✅ Clean up folder (30 sec)

**Total time**: 15-20 minutes (vs 1-2 hours manually!)

**Time saved**: 40-100 minutes per week! 🎉

---

## 📝 Weekly Checklist

Print this and tick off each week:

```
Week of: ________________

□ Exported invoices from iCompleat
□ Copied PDFs to invoices_to_process folder
□ Ran automation (double-click RUN_AUTOMATION)
□ Checked summary report
□ Reviewed flagged invoices (if any)
□ Fixed errors (if any)
□ Excel updated correctly
□ Approved invoices in iCompleat
□ Highlighted rows grey (optional)
□ Deleted processed PDFs from folder
□ Ready for next week!
```

---

**Questions?** Check SETUP_GUIDE.md or contact IT.
