#!/bin/bash
# ============================================================
# Invoice Automation - Mac Runner
# Double-click this file to process your invoices
# ============================================================

# Change to the script's directory
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "Invoice Processing Automation"
echo "============================================================"
echo ""

# Check if invoices_to_process folder exists
if [ ! -d "invoices_to_process" ]; then
    echo "ERROR: invoices_to_process folder not found!"
    echo "Please create it and add your invoice PDFs."
    echo ""
    read -p "Press any key to close..."
    exit 1
fi

# Count PDF files
count=$(ls -1 invoices_to_process/*.pdf 2>/dev/null | wc -l | tr -d ' ')

if [ "$count" -eq 0 ]; then
    echo "WARNING: No PDF files found in invoices_to_process folder!"
    echo ""
    echo "Please add your invoice PDFs to:"
    echo "$(pwd)/invoices_to_process"
    echo ""
    read -p "Press any key to close..."
    exit 1
fi

echo "Found $count invoice(s) to process"
echo ""
echo "Starting automation..."
echo ""

# Run the automation
python3 main.py process --input-dir ./invoices_to_process

echo ""
echo "============================================================"
echo "Processing complete!"
echo ""
echo "Check the reports in the 'output' folder:"
echo "- invoice_summary_*.csv (open in Excel)"
echo "- invoice_report_*.txt (detailed report)"
echo "============================================================"
echo ""

read -p "Press any key to close..."
