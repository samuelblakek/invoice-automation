# Deployment Guide

## Local Testing

1. Install Python 3.9+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the web app:
   ```bash
   streamlit run web_app.py
   ```
4. Browser opens automatically at `http://localhost:8501`
5. Test with example files in `example-files/`
6. Stop the server with `Ctrl+C`

---

## Streamlit Cloud (Recommended)

Free hosting, zero installation for end users, HTTPS encrypted.

### Step 1: Create a GitHub Repository

1. Create a GitHub account at https://github.com (if you don't have one)
2. Create a new **private** repository named `invoice-automation`
3. Upload the project files using GitHub Desktop or the web interface:
   - `web_app.py`, `requirements.txt`
   - `invoice_automation/` (entire folder)
   - Do **not** upload `example-files/` with real invoice data

### Step 2: Deploy to Streamlit Cloud

1. Go to https://streamlit.io/cloud and sign up with your GitHub account
2. Click "New app"
3. Select your repository, branch `main`, main file `web_app.py`
4. Click "Deploy"
5. Wait 2-3 minutes — you'll get a URL like `https://invoice-automation-abc123.streamlit.app`

Share that URL with your colleague. They can bookmark it and use it each week.

### Step 3: Updating the App

Push code changes to GitHub. Streamlit Cloud auto-detects changes and redeploys within 1-2 minutes.

---

## Password Protection (Optional)

1. In your Streamlit Cloud dashboard, go to your app's settings
2. Add a secret in the "Secrets" section:
   ```toml
   password = "your-secure-password-here"
   ```
3. Add this code at the top of `web_app.py`:
   ```python
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
4. Push changes to GitHub — Streamlit will auto-redeploy

---

## Alternative Hosting

### Heroku

1. Create a `Procfile`:
   ```
   web: sh setup.sh && streamlit run web_app.py
   ```
2. Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "[server]
   headless = true
   port = $PORT
   enableCORS = false
   " > ~/.streamlit/config.toml
   ```
3. Deploy:
   ```bash
   heroku login
   heroku create invoice-automation-yourcompany
   git push heroku main
   ```

### PythonAnywhere

1. Create an account at https://www.pythonanywhere.com
2. Upload files via the web interface
3. Configure per https://help.pythonanywhere.com/pages/StreamlitWebApps/

---

## Security & Data Handling

**Data flow:** Upload -> Process in memory -> Download -> Delete immediately

| Aspect | Status |
|--------|--------|
| Data storage | None — processed in memory only |
| Connection | HTTPS encrypted |
| File retention | Deleted after download |
| User accounts | Not required (anonymous) |
| Code visibility | Private GitHub repository |
| GDPR | Compliant — no data retention |

Best practices:
- Keep the GitHub repository **private**
- Don't store passwords or API keys in code (use Streamlit secrets)
- Share passwords securely (not via email)
- Update dependencies monthly (`pip list --outdated`)

---

## Troubleshooting

### "Module not found" error on Streamlit Cloud
Ensure `requirements.txt` is in the repository root and contains all dependencies.

### App won't load on Streamlit Cloud
Check logs: App dashboard -> Manage app -> View logs.

### "Repository not found"
Verify the repository is in your GitHub account and Streamlit Cloud has permission to access it.

### Excel file locked (local testing)
Close the Excel file in Excel before running the automation — openpyxl can't write to a locked file.

### All invoices fail to process
Check you uploaded the correct Excel files (Maintenance POs and Cost Centre Summary). Verify PO numbers exist in the spreadsheet.
