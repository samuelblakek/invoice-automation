# Invoice Automation - Quick Start

## 🎯 Choose Your Deployment

### Option A: Cloud-Based (RECOMMENDED)
**Best for:** Zero installation, works anywhere, easiest for non-technical users

**What you need:**
- GitHub account (free)
- Streamlit Cloud account (free)

**Time:** 30 minutes one-time setup

**Steps:**
1. Read `DEPLOYMENT_GUIDE.md` → "Option 1: Streamlit Cloud"
2. Follow the 4 steps to deploy
3. Get your URL (e.g., `https://invoice-automation.streamlit.app`)
4. Share URL with colleague
5. Give colleague `WEBAPP_USER_GUIDE.md`

**User experience:**
- Visit website
- Upload files
- Download results
- Done!

---

### Option B: Local Testing (For You First)
**Best for:** Testing before deploying to cloud

**What you need:**
- Python 3.9+ installed

**Time:** 5 minutes

**Steps:**
```bash
# 1. Install dependencies
pip install streamlit

# 2. Run the web app
streamlit run web_app.py

# 3. Browser opens automatically to http://localhost:8501

# 4. Test with example files in example-files/ folder
```

**Stop the server:** Press `Ctrl+C` in terminal

---

## 📁 Project Files Overview

### For Deployment (Upload to GitHub):
```
retail-support-automate-invoices/
├── web_app.py                    ← Main web application
├── main.py                       ← CLI version (alternative)
├── requirements.txt              ← Python dependencies
├── config.yaml                   ← Configuration (optional for web)
├── invoice_automation/           ← Core automation code
│   ├── extractors/              ← PDF extraction
│   ├── validators/              ← Validation logic
│   ├── processors/              ← Excel handling
│   ├── models/                  ← Data models
│   ├── utils/                   ← Utilities
│   ├── reports/                 ← Report generation
│   └── config/                  ← Configuration
└── example-files/               ← Test files (DON'T UPLOAD REAL DATA)
```

### Documentation Files:
```
├── DEPLOYMENT_GUIDE.md          ← How to deploy (for IT/you)
├── WEBAPP_USER_GUIDE.md         ← How to use (for colleague)
├── QUICK_START.md               ← This file
├── README.md                    ← Technical documentation
├── SETUP_GUIDE.md               ← CLI setup (if not using web)
├── USER_GUIDE.md                ← CLI guide (if not using web)
└── AMOUNT_EXTRACTION_FIXES.md   ← Technical details on fixes
```

---

## 🚀 Recommended Path

### For Non-Technical User (Your Colleague):

1. **You (Setup Person):**
   - Deploy to Streamlit Cloud (30 min)
   - Test with example files
   - Get the URL

2. **Share with Colleague:**
   - The URL
   - `WEBAPP_USER_GUIDE.md` file
   - Show them once (5 min demo)

3. **Colleague (Weekly):**
   - Visit URL
   - Upload files
   - Download results
   - ~20 minutes per week

**Total effort for colleague:** Zero setup, 20 min/week usage

---

## 🔍 Testing Checklist

Before sharing with colleague, test:

### ✅ Local Test:
```bash
streamlit run web_app.py
```
1. Upload 1-2 example PDFs
2. Upload example Excel files
3. Click "Process Invoices"
4. Check results make sense
5. Download updated Excel
6. Open Excel file - verify updates

### ✅ Cloud Test (After Deployment):
1. Visit your deployed URL
2. Repeat same test as local
3. Check it works on different devices:
   - Desktop/laptop
   - Different browsers (Chrome, Edge)
4. Try on phone/tablet (optional)

### ✅ User Acceptance Test:
1. Have colleague try it
2. Watch them use it once
3. Answer questions
4. Adjust documentation if needed

---

## 📋 Deployment Decision Tree

```
Do you have Windows security restrictions?
│
├─ YES → Use Cloud-Based (Streamlit Cloud)
│         ↓
│         Can you use GitHub (private repo)?
│         ├─ YES → Deploy to Streamlit Cloud ✅
│         └─ NO  → Ask IT for alternative hosting
│
└─ NO  → Your choice:
          ├─ Cloud-Based (easier for user) ✅
          └─ Local with web interface
```

---

## 💰 Cost Comparison

| Solution | Setup Cost | Monthly Cost | User Effort |
|----------|------------|--------------|-------------|
| **Streamlit Cloud** | Free | Free | Zero setup |
| **Local Web** | Free | Free | Install Python |
| **CLI (scripts)** | Free | Free | Install Python + learn commands |

**Recommendation:** Streamlit Cloud for your use case (free + easiest)

---

## 🎓 What Each File Does

### `web_app.py`
- Web interface with drag-and-drop
- Processes invoices in browser
- No command-line needed

### `main.py`
- Command-line version (alternative)
- For advanced users who prefer terminal
- Same functionality as web app

### `invoice_automation/`
- Core automation logic
- Shared by both web and CLI versions
- PDF extraction, validation, Excel updates

---

## 🔐 Security Considerations

### Data Flow:
```
User's Computer → Upload to Cloud → Process in Memory → Download → Delete
```

### What's Stored:
- ❌ No PDFs stored
- ❌ No Excel files stored
- ❌ No processing logs
- ✅ Only code is stored (in private GitHub repo)

### Access Control:
- Repository is private (only you see code)
- Can add password to web app (optional)
- HTTPS encrypted connection

### Compliance:
- GDPR compliant (no data retention)
- Suitable for business data
- Not suitable for: Highly classified data

---

## 🆘 If Something Goes Wrong

### During Deployment:
1. Check `DEPLOYMENT_GUIDE.md` troubleshooting section
2. Verify all files are in GitHub repository
3. Check Streamlit Cloud logs for errors
4. Try local testing first

### During Usage:
1. Check detailed report in web app
2. Verify Excel files are correct versions
3. Make sure PDFs are text-based (not scanned)
4. Contact setup person with screenshots

---

## 📞 Support Resources

### For Deployment Issues:
- Streamlit Docs: https://docs.streamlit.io
- Streamlit Forum: https://discuss.streamlit.io
- GitHub Docs: https://docs.github.com

### For Code Issues:
- Check `output/` folder for detailed reports
- Review `AMOUNT_EXTRACTION_FIXES.md` for known issues
- Check example files work correctly

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ Web app loads without errors
2. ✅ Example PDFs process successfully
3. ✅ Excel file updates correctly
4. ✅ NET amounts are accurate (ex-VAT)
5. ✅ £200+ authorization check works
6. ✅ Colleague can use it without help

---

## 📈 Next Steps After Deployment

### Week 1:
- User processes first batch
- You monitor for issues
- Collect feedback

### Week 2-4:
- User processes independently
- Check they're comfortable
- Address any questions

### Month 2+:
- Fully autonomous
- Check in monthly
- Update as needed

---

## 🔄 Maintenance Schedule

### Weekly: None
Users just use the website

### Monthly:
- Check for Python package updates
- Review usage/feedback
- Adjust if needed

### As Needed:
- Add new supplier formats
- Adjust validation rules
- Improve extractors

---

## 📝 Summary

**For Streamlit Cloud Deployment:**

1. Create GitHub account
2. Upload code to private repository
3. Create Streamlit Cloud account
4. Deploy app (3 clicks)
5. Share URL with colleague
6. Done!

**User Weekly Process:**
1. Visit URL
2. Upload PDFs + Excel files
3. Click process
4. Download results
5. ~20 minutes total

**Your Ongoing Effort:** ~5 minutes per month

---

**Ready to deploy?** Start with `DEPLOYMENT_GUIDE.md` → Option 1

**Questions?** All documentation is in this folder!
