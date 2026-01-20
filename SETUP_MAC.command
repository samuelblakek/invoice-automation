#!/bin/bash
# ============================================================
# Invoice Automation - Mac Setup
# Run this ONCE to install required components
# ============================================================

# Change to the script's directory
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "Invoice Automation - One-Time Setup"
echo "============================================================"
echo ""
echo "This will install the required components."
echo "This only needs to be run ONCE."
echo ""
echo "Please wait, this may take a few minutes..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo ""
    echo "Please install Python first:"
    echo "1. Go to https://www.python.org/downloads/"
    echo "2. Download and install Python 3"
    echo "3. Run this setup script again"
    echo ""
    read -p "Press any key to close..."
    exit 1
fi

echo "✓ Python is installed"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --quiet

# Install requirements
echo "Installing required packages..."
echo "(This may take 2-3 minutes)"
echo ""
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Installation failed!"
    echo ""
    echo "Please check your internet connection and try again."
    read -p "Press any key to close..."
    exit 1
fi

# Create necessary folders
echo ""
echo "Creating folders..."
mkdir -p invoices_to_process
mkdir -p output
mkdir -p backups

# Make command file executable
chmod +x RUN_AUTOMATION.command

echo ""
echo "============================================================"
echo "✓ Setup complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml to set your file paths"
echo "2. Copy your invoice PDFs to the invoices_to_process folder"
echo "3. Double-click RUN_AUTOMATION.command to process invoices"
echo ""
echo "See USER_GUIDE.md for detailed instructions."
echo "============================================================"
echo ""

read -p "Press any key to close..."
