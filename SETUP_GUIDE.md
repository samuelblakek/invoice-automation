# Invoice Automation - Setup Guide

## For Non-Technical Users (One-Time Setup)

This guide will help you set up the invoice automation on your computer. You only need to do this **once**.

---

## Step 1: Install Python (5 minutes)

### On Windows:

1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python" button
3. **IMPORTANT**: When the installer opens, **CHECK THE BOX** that says "Add Python to PATH"
4. Click "Install Now"
5. Wait for installation to complete
6. Click "Close"

### On Mac:

1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.x.x" (whatever the latest version is)
3. Open the downloaded file
4. Follow the installation steps (just keep clicking "Continue" and "Install")
5. Enter your Mac password when asked
6. Click "Close" when done

---

## Step 2: Download the Automation Files

1. Someone (IT or your colleague) will give you a folder called `retail-support-automate-invoices`
2. Put this folder somewhere easy to find, like:
   - **Windows**: `C:\invoice-automation\`
   - **Mac**: Your Documents folder

---

## Step 3: Run the Setup Script (One Time Only)

### On Windows:

1. Open the `retail-support-automate-invoices` folder
2. **Double-click** the file called `SETUP_WINDOWS.bat`
3. A black window will appear - **don't close it!**
4. Wait until you see "Setup complete! You can close this window."
5. Press any key to close the window

### On Mac:

1. Open the `retail-support-automate-invoices` folder
2. **Double-click** the file called `SETUP_MAC.command`
3. If you see a security warning:
   - Go to System Preferences → Security & Privacy
   - Click "Open Anyway"
4. A terminal window will appear - **don't close it!**
5. Wait until you see "Setup complete! You can close this window."
6. Press any key to close the window

---

## Step 4: Configure Your File Paths

1. Open the `retail-support-automate-invoices` folder
2. Open the file called `config.yaml` (right-click → Open With → TextEdit/Notepad)
3. Change these lines to point to YOUR files:

```yaml
paths:
  # Change this to where your Maintenance PO spreadsheet is saved
  maintenance_workbook: "C:/Users/YourName/Documents/Maintenance POs.xlsx"

  # Change this to where your Cost Centre Summary is saved
  cost_centre_summary: "C:/Users/YourName/Documents/Cost Centre Summary.xlsx"

  # Leave these as they are (they're folders)
  invoices_input_dir: "./invoices_to_process"
  output_dir: "./output"
```

**Important**:
- Use forward slashes `/` even on Windows (not backslashes `\`)
- Replace `YourName` with your actual Windows username
- Make sure the file paths are correct!

4. Save and close the file

---

## Step 5: Test It Works

1. Create a folder called `test_invoices` in the automation folder
2. Copy one of the example PDFs into `test_invoices`
3. **Double-click** `RUN_AUTOMATION.bat` (Windows) or `RUN_AUTOMATION.command` (Mac)
4. You should see a window showing the processing
5. Check the `output` folder for a report

**If it worked**: You're all set! 🎉

**If you see errors**:
- Check your file paths in `config.yaml` are correct
- Make sure your Excel files aren't open
- Contact IT for help

---

## Troubleshooting

### "Python is not recognized" error
- You didn't check "Add Python to PATH" during installation
- Reinstall Python and make sure to check that box

### "Permission denied" error (Mac)
- Right-click the .command file → Get Info
- Under "Sharing & Permissions", make sure you can "Read & Write"

### Excel file locked error
- Close the Maintenance PO Excel file before running automation
- Don't have it open in Excel

### No invoices found
- Make sure PDFs are in the `invoices_to_process` folder
- PDFs must end with `.pdf`

---

## Getting Help

If you're stuck:

1. Take a screenshot of any error messages
2. Check the `output/invoice_report_YYYYMMDD.txt` file for details
3. Send both to IT or the person who set this up for you

---

## Next Steps

Once setup is complete, go to **USER_GUIDE.md** to learn how to use the automation weekly.
