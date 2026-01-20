@echo off
REM ============================================================
REM Invoice Automation - Windows Setup
REM Run this ONCE to install required components
REM ============================================================

echo.
echo ============================================================
echo Invoice Automation - One-Time Setup
echo ============================================================
echo.
echo This will install the required components.
echo This only needs to be run ONCE.
echo.
echo Please wait, this may take a few minutes...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python first:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download and install Python
    echo 3. IMPORTANT: Check "Add Python to PATH" during installation
    echo 4. Run this setup script again
    echo.
    pause
    exit /b 1
)

echo ✓ Python is installed
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo Installing required packages...
echo (This may take 2-3 minutes)
echo.
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed!
    echo.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

REM Create necessary folders
echo.
echo Creating folders...
if not exist "invoices_to_process\" mkdir invoices_to_process
if not exist "output\" mkdir output
if not exist "backups\" mkdir backups

echo.
echo ============================================================
echo ✓ Setup complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Edit config.yaml to set your file paths
echo 2. Copy your invoice PDFs to the invoices_to_process folder
echo 3. Double-click RUN_AUTOMATION.bat to process invoices
echo.
echo See USER_GUIDE.md for detailed instructions.
echo ============================================================
echo.

pause
