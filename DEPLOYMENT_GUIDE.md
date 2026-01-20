# Invoice Automation - Deployment Guide

## Option 1: Streamlit Cloud (RECOMMENDED - Free & Easy)

**Perfect for:** Non-technical users, zero installation required

### What is Streamlit Cloud?
- Free hosting for web apps
- No installation needed for users
- Users just visit a URL
- Automatic HTTPS encryption
- No credit card required

### Deployment Steps (One-Time Setup)

#### Step 1: Create GitHub Account (5 minutes)
1. Go to https://github.com
2. Click "Sign up"
3. Choose a username (e.g., "yourcompany-automation")
4. Verify your email

#### Step 2: Upload Code to GitHub (10 minutes)
1. On GitHub, click the "+" in top right → "New repository"
2. Name it: `invoice-automation`
3. Set to **Private** (important for security)
4. Click "Create repository"
5. Download the GitHub Desktop app: https://desktop.github.com
6. Install and sign in
7. Click "Add" → "Add existing repository"
8. Select your `retail-support-automate-invoices` folder
9. Click "Publish repository"
10. Make sure "Keep this code private" is checked
11. Click "Publish"

**Alternative (Without GitHub Desktop):**
1. On the repository page, click "Add file" → "Upload files"
2. Drag and drop all files from `retail-support-automate-invoices` folder
3. Click "Commit changes"

#### Step 3: Deploy to Streamlit Cloud (5 minutes)
1. Go to https://streamlit.io/cloud
2. Click "Sign up" and use your GitHub account
3. Click "New app"
4. Select:
   - Repository: `yourcompany-automation/invoice-automation`
   - Branch: `main`
   - Main file path: `web_app.py`
5. Click "Deploy!"
6. Wait 2-3 minutes for deployment

#### Step 4: Get Your URL
Once deployed, you'll get a URL like:
```
https://invoice-automation-abc123.streamlit.app
```

**Share this URL with your colleague** - that's it! They can bookmark it.

### Security Notes for Streamlit Cloud:
- ✅ Connection is HTTPS encrypted
- ✅ No data is stored (processed in memory only)
- ✅ Repository is private (only you can see code)
- ✅ Can add password protection (see below)

### Adding Password Protection (Optional):
1. Create a file `.streamlit/secrets.toml` in your repository:
```toml
password = "your-secure-password-here"
```

2. Add this code at the top of `web_app.py`:
```python
import streamlit as st

# Password protection
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if password == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
```

3. Push changes to GitHub
4. Streamlit will auto-redeploy

---

## Option 2: Local Web Interface (For Testing)

**Perfect for:** Testing before deploying to cloud

### Setup (5 minutes)
1. Install Python (see SETUP_GUIDE.md)
2. Open terminal/command prompt
3. Navigate to the folder:
   ```bash
   cd path/to/retail-support-automate-invoices
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

### Run Locally
```bash
streamlit run web_app.py
```

Your browser will automatically open to `http://localhost:8501`

**To stop:** Press `Ctrl+C` in the terminal

---

## Option 3: Heroku (Alternative Free Hosting)

**Perfect for:** If Streamlit Cloud doesn't work for some reason

### Steps:
1. Create account at https://heroku.com
2. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
3. Create files:

**Procfile:**
```
web: sh setup.sh && streamlit run web_app.py
```

**setup.sh:**
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

4. Deploy:
```bash
heroku login
heroku create invoice-automation-yourcompany
git push heroku main
```

---

## Option 4: PythonAnywhere (Another Alternative)

**Perfect for:** UK-based hosting, free tier available

### Steps:
1. Create account at https://www.pythonanywhere.com
2. Upload files via web interface
3. Set up web app in dashboard
4. Configure WSGI file for Streamlit

See: https://help.pythonanywhere.com/pages/StreamlitWebApps/

---

## Comparison Table

| Option | Cost | Setup Time | Best For | Data Storage |
|--------|------|------------|----------|--------------|
| **Streamlit Cloud** | Free | 20 min | Non-technical users | None (in-memory) |
| **Local Web** | Free | 5 min | Testing only | None |
| **Heroku** | Free tier | 30 min | Alternative to Streamlit | None |
| **PythonAnywhere** | Free tier | 30 min | UK hosting | None |

---

## Updating the App

### If Using Streamlit Cloud:
1. Make changes to code locally
2. Push to GitHub (using GitHub Desktop or web interface)
3. Streamlit Cloud auto-detects changes and redeploys
4. Wait 1-2 minutes

### If Using Local:
1. Make changes to code
2. Save files
3. Streamlit auto-reloads in browser

---

## Troubleshooting Deployment

### "Module not found" Error
**Fix:** Make sure `requirements.txt` is in the repository root

### "App is not loading"
**Fix:** Check Streamlit Cloud logs:
1. Go to your app dashboard
2. Click "Manage app"
3. View logs for errors

### "Too many requests"
**Fix:** Streamlit Cloud free tier has limits:
- Check usage in dashboard
- Consider upgrading if needed
- Or deploy to own server

### "Repository not found"
**Fix:** Make sure repository is accessible:
1. Check it's in your GitHub account
2. Verify Streamlit Cloud has permission
3. Re-authenticate if needed

---

## Security Best Practices

### For Streamlit Cloud Deployment:

1. **Keep Repository Private**
   - Never make it public
   - Contains business logic

2. **Don't Store Credentials**
   - No passwords in code
   - No API keys in code
   - Use Streamlit secrets for configs

3. **Add Password Protection**
   - See password protection section above
   - Share password securely (not via email)

4. **Monitor Usage**
   - Check Streamlit Cloud analytics
   - Look for unusual activity

5. **Regular Updates**
   - Update dependencies monthly
   - Check for security patches

### Data Handling:

- ✅ Files processed in memory
- ✅ Deleted after session ends
- ✅ No logging of file contents
- ✅ HTTPS encryption
- ❌ Files NOT stored on disk
- ❌ No database
- ❌ No persistent storage

---

## Cost Breakdown

### Free Tier Limits:

**Streamlit Cloud (Free):**
- 1 private app
- Unlimited public apps
- 1 GB storage
- Shared resources
- Community support

**Paid (if needed):**
- $20/month per developer
- Unlimited private apps
- Priority support
- More resources

### Recommendation:
Start with free tier. Only upgrade if:
- Processing >100 invoices per session
- Need faster processing
- Want dedicated support

---

## Maintenance

### Weekly:
- Nothing! Users just visit the URL

### Monthly:
- Check for Python package updates:
  ```bash
  pip list --outdated
  ```
- Update if security patches available

### As Needed:
- Add new supplier extractors if formats change
- Adjust validation rules if policies change
- Update based on user feedback

---

## Getting Help

### Streamlit Cloud Issues:
- Docs: https://docs.streamlit.io
- Forum: https://discuss.streamlit.io
- Email: support@streamlit.io

### Code Issues:
- Check `output/invoice_report_*.txt` for detailed errors
- Review this guide's troubleshooting section
- Contact the developer who set this up

---

## Next Steps

1. ✅ Choose deployment option (Streamlit Cloud recommended)
2. ✅ Follow deployment steps above
3. ✅ Test with example files
4. ✅ Share URL with colleague
5. ✅ Provide them with WEBAPP_USER_GUIDE.md

---

**Estimated Total Setup Time:** 30 minutes for Streamlit Cloud deployment

**Ongoing Maintenance:** ~5 minutes per month
