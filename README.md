# 📄 Invoice Processing Automation

> Automated invoice processing system with web interface - Zero installation required!

Transform your weekly invoice processing from **2 hours of manual work** to **20 minutes of automation**. Extracts invoice data from PDFs, validates against Purchase Orders, checks £200+ authorizations, and auto-updates Excel spreadsheets.

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Extraction** | Automatically extracts data from AAW, CJL, APS, Amazon, Compco invoices |
| ✅ **PO Matching** | Finds and validates matching Purchase Order records |
| ⚠️ **£200+ Authorization** | Critical check - validates quote authorization (company policy) |
| 📊 **Excel Updates** | Auto-updates spreadsheets while preserving all formatting & formulas |
| 📋 **Detailed Reports** | Shows what was updated and what needs manual review |
| 🔒 **Secure Processing** | No data stored - everything processed in memory |

---

## 🚀 Quick Start

### Web Interface (Recommended)

**Perfect for non-technical users** - No installation required!

1. **Visit the web app:** `https://your-app-name.streamlit.app`
2. **Upload files:**
   - Invoice PDFs
   - Maintenance PO Excel spreadsheet
   - Cost Centre Summary Excel file
3. **Click "Process Invoices"**
4. **Download results:**
   - Updated Excel file
   - CSV summary
   - Detailed report

**That's it!** See [WEBAPP_USER_GUIDE.md](WEBAPP_USER_GUIDE.md) for detailed instructions.

### Command Line Interface (Alternative)

For advanced users who prefer terminal:

```bash
# Install
pip install -r requirements.txt

# Process invoices
python main.py process --input-dir ./invoices_to_process

# Dry-run (preview only)
python main.py process --input-dir ./invoices_to_process --dry-run
```

---

## 📚 Documentation

| Document | For | Description |
|----------|-----|-------------|
| [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) | **Start Here** | Complete overview and deployment guide |
| [QUICK_START.md](QUICK_START.md) | Setup Person | 5-minute quick start guide |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | IT/Setup | Detailed deployment to Streamlit Cloud |
| [WEBAPP_USER_GUIDE.md](WEBAPP_USER_GUIDE.md) | **End User** | How to use the web interface (give to colleague) |
| [USER_GUIDE.md](USER_GUIDE.md) | CLI Users | Command-line version guide |
| [AMOUNT_EXTRACTION_FIXES.md](AMOUNT_EXTRACTION_FIXES.md) | Technical | Details on NET amount extraction fixes |

---

## ⚡ How It Works

```
📄 Upload PDFs + Excel Files
   ↓
🔍 Extract Invoice Data
   → Invoice number, PO number, amounts, store, supplier
   ↓
🔎 Find Matching PO
   → Search correct Excel sheet based on supplier
   ↓
✅ Validate Everything
   ✓ PO exists and not already invoiced
   ✓ Store name matches (fuzzy matching)
   ✓ Nominal code correct
   ✓ If >£200, quote MUST be authorized ← CRITICAL
   ✓ Amount valid
   ↓
📝 Update Excel
   → INVOICE NO., INVOICE AMOUNT (EX VAT), INVOICE SIGNED
   ↓
📊 Generate Reports
   → Updated Excel + CSV summary + Detailed report
   ↓
🗑️ Delete Everything
   → No data stored online
```

---

## 🎯 Supported Suppliers

- ✅ **AAW National Shutters** - Sheet: AAW NATIONAL (PANDA)
- ✅ **CJL Group** - Sheet: CJL
- ✅ **APS Fire Systems** - Sheet: APS
- ✅ **Amazon Business** - Sheet: ORDERS
- ✅ **Compco Fire Systems** - Sheet: OTHER
- ✅ **Aura Air Conditioning** - Sheet: AURA AC
- ✅ **Generic** - Any other supplier

---

## ⚠️ Critical £200+ Authorization Check

**Company Policy Enforcement:**

For invoices over £200 (ex-VAT):
1. ✓ "QUOTE OVER £200" column must have a value
2. ✓ "AUTHORISED" column must have a value
3. ❌ **Auto-update BLOCKED** if authorization missing

**Example:**
- Invoice: £518.00 (ex-VAT)
- Quote: "Q12345", Authorized: "John Smith" → ✅ **PASS**
- Quote: "Q12345", Authorized: *empty* → ❌ **BLOCKED**
- Quote: *empty* → ❌ **BLOCKED**

This ensures compliance before payment processing.

---

## 💡 What Gets Updated

**Only 3 columns** in matching PO rows:

| Column | Updated To |
|--------|------------|
| INVOICE NO. | Invoice number from PDF |
| INVOICE AMOUNT (EX VAT) | Net amount (excluding VAT) |
| INVOICE SIGNED | Today's date |

**Everything else preserved:**
- ✅ All formulas
- ✅ Cell formatting
- ✅ Conditional formatting
- ✅ Other columns
- ✅ Other sheets

---

## 🔒 Security & Privacy

| Aspect | Status |
|--------|--------|
| Data Storage | ❌ None - processed in memory only |
| Connection | ✅ HTTPS encrypted |
| File Retention | ❌ Deleted after download |
| User Accounts | ❌ Not required - anonymous |
| Code Visibility | 🔒 Private GitHub repository |
| GDPR Compliant | ✅ Yes - no data retention |

**Data Flow:** Upload → Process in Memory → Download → Delete Immediately

---

## 📊 Expected Results

**Typical Weekly Processing:**

```
Input:  15 invoice PDFs + 2 Excel files
Time:   30-60 seconds processing
Output:
  ✅ 12 auto-updated (80%)
  ⚠️  2 flagged for review (13%)
  ❌ 1 failed (7%)
```

**Time Savings:** 40-100 minutes per week!

---

## 🛠️ Project Structure

```
invoice-automation/
├── web_app.py                    ← Web interface (MAIN)
├── main.py                       ← CLI version (alternative)
├── requirements.txt              ← Python dependencies
├── config.yaml                   ← Configuration
├── invoice_automation/           ← Core automation logic
│   ├── extractors/              ← PDF extraction (per supplier)
│   ├── validators/              ← Validation logic
│   ├── processors/              ← Excel reading/writing
│   ├── models/                  ← Data structures
│   ├── utils/                   ← Helper functions
│   └── reports/                 ← Report generation
└── example-files/               ← Test data
```

---

## 🚀 Deployment Options

### Option 1: Streamlit Cloud (Recommended)
- ✅ Free hosting
- ✅ Zero installation for users
- ✅ Access from anywhere
- ✅ HTTPS encrypted
- **Setup:** 30 minutes one-time
- **See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Option 2: Local Web Interface
- ✅ Run on your computer
- ✅ Web browser interface
- ⚠️ Requires Python installed
- **Setup:** 5 minutes
- **Run:** `streamlit run web_app.py`

### Option 3: Command Line
- ✅ Advanced users
- ✅ Automation/scripting
- ⚠️ Requires Python installed
- **Setup:** 5 minutes
- **Run:** `python main.py process --input-dir ./invoices`

---

## 📈 Success Metrics

**After 1 Week:**
- ✅ First batch processed successfully
- ✅ Time saved: ~1 hour

**After 1 Month:**
- ✅ Independent usage
- ✅ Minimal questions
- ✅ Time saved: ~6-10 hours

**After 3 Months:**
- ✅ Fully autonomous
- ✅ Part of normal workflow
- ✅ ~40-100 min saved per week

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "PO not found" | Verify PO exists in spreadsheet, check correct sheet |
| "Quote not authorized" | Add authorization to "AUTHORISED" column for £200+ invoices |
| "Store mismatch" | Fuzzy matching being cautious - usually safe to update manually |
| "Amounts wrong" | Automation extracts NET (ex-VAT) - this is correct! |

See detailed troubleshooting in [WEBAPP_USER_GUIDE.md](WEBAPP_USER_GUIDE.md)

---

## 💰 Cost

| Component | Cost |
|-----------|------|
| Streamlit Cloud Hosting | **Free** |
| GitHub Repository | **Free** (private) |
| Python & Dependencies | **Free** |
| **Total** | **£0.00** 🎉 |

---

## 🔄 Maintenance

| Frequency | Task | Time |
|-----------|------|------|
| Weekly | None - users just use it | 0 min |
| Monthly | Check for package updates | 5 min |
| As Needed | Add new supplier formats | 30 min |

**Total effort:** ~5 minutes per month

---

## 🎓 Technical Details

**Tech Stack:**
- Python 3.9+
- Streamlit (web interface)
- pdfplumber (PDF extraction)
- pandas + openpyxl (Excel handling)
- fuzzywuzzy (fuzzy matching)

**NET Amount Extraction:**
- ✅ Extracts NET (ex-VAT) amounts correctly
- ✅ Never picks up totals that include VAT
- ✅ Handles multiple invoice formats
- ✅ See [AMOUNT_EXTRACTION_FIXES.md](AMOUNT_EXTRACTION_FIXES.md) for details

---

## 📞 Support

**For Deployment:** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**For Usage:** See [WEBAPP_USER_GUIDE.md](WEBAPP_USER_GUIDE.md)
**For Code Issues:** Check detailed reports in `output/` folder

---

## 🎉 Ready to Deploy?

1. **Read:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Complete overview
2. **Deploy:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Step-by-step guide
3. **Use:** [WEBAPP_USER_GUIDE.md](WEBAPP_USER_GUIDE.md) - Give to end user

**Deployment Time:** 30 minutes
**User Training:** 5 minutes
**Weekly Time Savings:** 40-100 minutes

---

## 📄 License

Private use only. Not for distribution.

---

**Built with ❤️ for efficient invoice processing**

**Questions?** Check the documentation - all answers are there!
