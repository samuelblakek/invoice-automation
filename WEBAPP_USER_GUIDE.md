# Invoice Automation - Web App User Guide

## For Non-Technical Users (Weekly Process)

This guide shows you how to use the **web-based** invoice automation. No installation needed!

---

## 🌐 Accessing the Automation

### Your URL
Your automation is available at:
```
https://[your-app-name].streamlit.app
```

**Bookmark this URL!** You'll use it every week.

### Browser Compatibility
Works in any modern browser:
- ✅ Google Chrome (recommended)
- ✅ Microsoft Edge
- ✅ Firefox
- ✅ Safari

---

## 📋 Weekly Workflow (5 Steps, ~10 minutes)

### Step 1: Export Invoices from iCompleat
1. Log into iCompleat (your usual process)
2. Export invoices as PDFs
3. Save them somewhere on your computer (e.g., Desktop or Downloads)

**Time:** 5 minutes

---

### Step 2: Open the Automation Website
1. Click your bookmarked URL or type it in your browser
2. The page will load with the title "Invoice Processing Automation"
3. You'll see three tabs: "Process Invoices", "About", "Help"

**Time:** 10 seconds

---

### Step 3: Upload Your Files

#### 📄 Invoice PDFs (Left side)
1. Look for the section titled "Invoice PDFs"
2. Click "Browse files" or **drag and drop** your PDF files
3. You can select multiple PDFs at once:
   - Windows: Hold `Ctrl` and click each file
   - Mac: Hold `Cmd` and click each file
4. Green checkmark appears: "✓ X invoice(s) uploaded"

**Example files you might upload:**
- AAW invoice 12345.pdf
- CJL Invoice 67890.pdf
- Amazon Invoice ABC123.pdf

#### 📊 Excel Files (Right side)
You need to upload **2 Excel files** every time:

1. **Maintenance PO Spreadsheet:**
   - Click "Browse files" under "Maintenance PO Spreadsheet"
   - Select your file (e.g., "Maintenance PO's - April 2025.xlsx")
   - Green checkmark appears

2. **Cost Centre Summary:**
   - Click "Browse files" under "Cost Centre Summary"
   - Select your file (e.g., "Cost Centre Summary.xlsx")
   - Green checkmark appears

**Important:** Make sure you have the **latest versions** of these Excel files from your network drive!

**Time:** 2 minutes

---

### Step 4: Process Invoices
1. Once all files are uploaded, the "🚀 Process Invoices" button turns blue
2. Click the blue "Process Invoices" button
3. A progress bar appears with "Processing invoices..."
4. Wait 30-60 seconds (don't close the browser!)
5. You'll see "✅ Processing Complete!"

**What's happening behind the scenes:**
- Extracting data from PDFs
- Finding matching PO records
- Checking £200+ authorizations
- Validating amounts
- Updating your spreadsheet

**Time:** 1 minute

---

### Step 5: Review Results

#### Summary Cards (Top)
You'll see 4 boxes showing:
- **Total Invoices:** How many you uploaded
- **Auto-Updated:** Successfully processed ✅
- **Needs Review:** Flagged for manual check ⚠️
- **Failed:** Couldn't process ❌

#### Invoice Details Table
Below the summary, you'll see a table with all invoices:

| Status | Invoice # | Supplier | PO # | Store | Amount | Issues |
|--------|-----------|----------|------|-------|--------|--------|
| ✅ | 5002746 | AAW | PS03... | Maidstone | £116.50 | None |
| ⚠️ | 28564 | CJL | CJL316 | Portsmouth | £518.00 | Quote not auth... |

**Status icons:**
- ✅ Green checkmark = Auto-updated successfully
- ⚠️ Warning triangle = Needs your attention
- ❌ Red X = Failed to process

**Time:** 1 minute to review

---

### Step 6: Download Updated Files

You'll see 3 download buttons:

#### 📊 Download Updated Excel (MOST IMPORTANT)
1. Click "📊 Download Updated Excel"
2. File downloads to your Downloads folder
3. Name: `Maintenance_POs_Updated_20260120_143052.xlsx`
4. **This is your updated spreadsheet** - save it to your network drive!

#### 📄 Download CSV Summary (Optional)
- Spreadsheet with summary you can open in Excel
- Good for record-keeping

#### 📝 Download Detailed Report (Optional)
- Text file with all validation details
- Use this if you need to understand why something failed

**Time:** 30 seconds

---

### Step 7: Handle Issues (If Any)

If some invoices show ⚠️ or ❌:

#### Click "View Issues" dropdown
This shows exactly what's wrong:

**Common Issues:**

1. **"PO number not found"**
   - **Why:** PO doesn't exist in your spreadsheet yet
   - **Fix:** Add the PO manually, or process this invoice manually

2. **"PO already invoiced"**
   - **Why:** This PO already has an invoice number
   - **Fix:** Check if it's a duplicate or different invoice

3. **"Quote authorization missing"** (Over £200)
   - **Why:** Invoice is over £200 but quote not authorized
   - **Fix:** Get authorization, update Excel, run automation again

4. **"Store name doesn't match"**
   - **Why:** Invoice shows different store name than PO
   - **Fix:** Usually safe to update manually (fuzzy matching being cautious)

For invoices that failed, you can:
- Fix the issue in your Excel file
- Upload files again and reprocess
- Or handle manually as you normally would

**Time:** 5-10 minutes (only if issues exist)

---

### Step 8: Final Steps (Still Manual)

The automation **CANNOT** do these steps:

1. ✅ **Save the updated Excel file** to your network drive
2. ✅ **Approve invoices in iCompleat** (your usual process)
3. ✅ **Highlight completed rows grey** (optional)

**Time:** 5 minutes

---

## 🎨 Visual Walkthrough

```
┌─────────────────────────────────────────────────┐
│  INVOICE AUTOMATION WEBSITE                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  📄 Invoice PDFs          📊 Excel Files        │
│  [Drag & drop here]       [Upload Maintenance]  │
│                           [Upload Cost Centre]  │
│                                                  │
│         [🚀 Process Invoices]                   │
│                                                  │
│  ✅ Processing Complete!                        │
│                                                  │
│  Total: 10  Auto: 8  Review: 2  Failed: 0      │
│                                                  │
│  [Invoice Details Table]                        │
│                                                  │
│  [📊 Download Excel] [📄 CSV] [📝 Report]      │
└─────────────────────────────────────────────────┘
```

---

## 💡 Tips & Best Practices

### Tip 1: Process in Batches
- Don't wait for 50 invoices
- Process 10-20 at a time
- Easier to spot and fix errors

### Tip 2: Keep Excel Files Updated
- Always upload the **latest** Excel files
- Don't use old versions from last week
- Get them fresh from your network drive

### Tip 3: Use Chrome
- Google Chrome works best with the web app
- If you have issues, try Chrome

### Tip 4: Don't Close Browser Too Soon
- Wait for "Processing Complete" message
- Don't close browser while processing
- Don't refresh the page

### Tip 5: Check Summary First
- Look at the numbers before downloading
- If "Auto-Updated" = "Total", everything worked!
- If "Failed" > 0, check the issues section

### Tip 6: Keep Downloaded Files Organized
- Create a folder like "Invoice Automation - 2025"
- Save weekly Excel files with dates
- Keep CSV summaries for records

---

## ⚠️ Common Mistakes to Avoid

### ❌ Uploading Wrong Excel Files
**Problem:** Using last week's Excel file
**Solution:** Always get fresh files from network drive

### ❌ Forgetting to Download Updated Excel
**Problem:** Clicking away without downloading
**Solution:** Always download the updated Excel file!

### ❌ Not Checking Results
**Problem:** Assuming everything worked
**Solution:** Always review the summary and issues

### ❌ Processing Same Invoices Twice
**Problem:** Running automation on already-processed invoices
**Solution:** POs with existing invoice numbers will be flagged as duplicates

### ❌ Closing Browser Too Soon
**Problem:** Browser closed during processing
**Solution:** Wait for "Processing Complete" message

---

## 🔒 Security & Privacy

### Your Data is Safe:
- ✅ Connection is HTTPS encrypted (padlock in browser)
- ✅ Files processed in memory only
- ✅ Nothing saved on servers
- ✅ Files deleted immediately after download
- ✅ No one else can see your invoices

### What Happens to Uploaded Files:
1. You upload → Files stay in browser memory
2. Processing happens → Still in memory
3. You download results → Memory cleared
4. You close browser → Everything deleted

**Bottom line:** Your data never leaves your control except during the brief processing period.

---

## 📊 Understanding the Results

### What Gets Updated in Excel:
The automation only updates **3 columns** in matching PO rows:

| Column | Updated To |
|--------|------------|
| INVOICE NO. | Invoice number from PDF |
| INVOICE AMOUNT (EX VAT) | Net amount (excluding VAT) |
| INVOICE SIGNED | Today's date |

**Everything else** in your Excel file stays exactly the same:
- Formulas preserved
- Formatting preserved
- Other columns unchanged
- No rows added or deleted

### Validation Checks Performed:
For **every** invoice, the automation checks:
1. ✓ PO exists in spreadsheet
2. ✓ PO not already invoiced
3. ✓ Store name matches
4. ✓ Nominal code correct
5. ✓ If >£200, quote authorized ⚠️ CRITICAL
6. ✓ Amount is valid

**All checks must pass** for auto-update. If any fail, flagged for review.

---

## 🆘 Troubleshooting

### Problem: Website won't load
**Try:**
1. Refresh the page (F5 or Ctrl+R)
2. Clear browser cache
3. Try a different browser
4. Check your internet connection

### Problem: "Upload failed" error
**Try:**
1. Check file isn't open in Excel
2. Make sure it's a .xlsx file (not .xls or .csv)
3. File size must be under 200MB
4. Try uploading one file at a time

### Problem: All invoices failed
**Check:**
1. Did you upload the correct Excel files?
2. Are the file paths in Excel correct?
3. Do the PO numbers exist in your spreadsheet?

### Problem: Processing stuck at 99%
**Wait:**
- Large files take longer
- Don't refresh the page
- If stuck >5 minutes, refresh and try again

### Problem: Downloaded Excel won't open
**Fix:**
1. Make sure you fully downloaded it
2. Check Downloads folder
3. File might be blocked - right-click → Properties → Unblock
4. Try opening in Excel (not double-click)

---

## 📞 Getting Help

### Before Asking for Help:
1. ✅ Check the "View Issues" section for error details
2. ✅ Download the detailed report (📝 button)
3. ✅ Take screenshots of any errors
4. ✅ Note which invoice(s) failed

### Who to Contact:
- **For website not loading:** IT department
- **For invoice processing issues:** Person who set this up
- **For Excel/iCompleat questions:** Your usual support

### What to Include When Asking for Help:
1. Screenshot of error message
2. Which invoice(s) failed (invoice numbers)
3. What you were trying to do
4. The detailed report file (if downloaded)

---

## ✅ Weekly Checklist

Print this and check off each week:

```
Week of: ________________

Pre-Processing:
□ Downloaded latest Excel files from network drive
□ Exported invoices from iCompleat as PDFs
□ Have 10-20 invoices ready (don't batch too many)

Processing:
□ Opened automation website
□ Uploaded all invoice PDFs
□ Uploaded Maintenance PO spreadsheet
□ Uploaded Cost Centre Summary
□ Clicked "Process Invoices"
□ Waited for "Processing Complete"

Review:
□ Checked summary numbers
□ Reviewed invoice details table
□ Checked for any issues (⚠️ or ❌)
□ Downloaded updated Excel file
□ Downloaded CSV summary (optional)
□ Saved files to network drive

Post-Processing:
□ Fixed any flagged invoices (if needed)
□ Approved invoices in iCompleat
□ Highlighted rows grey (optional)
□ Ready for next week!

Time saved this week: _______ minutes
```

---

## 🎓 Understanding Amounts

### Why "Net Amount"?
The automation extracts **NET (ex-VAT)** amounts because:
- This is what goes in "INVOICE AMOUNT (EX VAT)" column
- This is what you need for PO matching
- VAT is separate

### Example:
- Invoice shows: "Total £139.80"
- But also shows: "Net £116.50" and "VAT £23.30"
- **Automation extracts: £116.50** ✅
- This is correct!

### If Amount Looks Wrong:
1. Check the PDF - what does "Net Total" or "Sub Total" say?
2. It should **NOT** include VAT
3. If automation got it wrong, download detailed report and contact support

---

## 🎉 Success!

You've completed the weekly invoice processing!

**Time Breakdown:**
- Export from iCompleat: 5 min
- Upload to website: 2 min
- Processing: 1 min
- Review & download: 2 min
- Fix issues (if any): 5 min
- iCompleat approval: 5 min

**Total: ~20 minutes** (vs 1-2 hours manually!)

**You saved: 40-100 minutes!** 🎉

---

## 📖 Additional Resources

- **DEPLOYMENT_GUIDE.md** - How the website was set up (for IT)
- **README.md** - Technical documentation
- **Help tab** - In the website itself, click "Help" tab

---

**Questions?** Check the Help tab in the web app or contact your IT support.

**Feedback?** Let the person who set this up know what's working and what could be improved!
