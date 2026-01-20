@echo off
REM ============================================================
REM Invoice Automation - Windows Runner
REM Double-click this file to process your invoices
REM ============================================================

echo.
echo ============================================================
echo Invoice Processing Automation
echo ============================================================
echo.

REM Check if invoices_to_process folder exists
if not exist "invoices_to_process\" (
    echo ERROR: invoices_to_process folder not found!
    echo Please create it and add your invoice PDFs.
    echo.
    pause
    exit /b 1
)

REM Count PDF files
set count=0
for %%f in (invoices_to_process\*.pdf) do set /a count+=1

if %count%==0 (
    echo WARNING: No PDF files found in invoices_to_process folder!
    echo.
    echo Please add your invoice PDFs to:
    echo %cd%\invoices_to_process
    echo.
    pause
    exit /b 1
)

echo Found %count% invoice(s) to process
echo.
echo Starting automation...
echo.

REM Run the automation
python main.py process --input-dir ./invoices_to_process

echo.
echo ============================================================
echo Processing complete!
echo.
echo Check the reports in the 'output' folder:
echo - invoice_summary_*.csv (open in Excel)
echo - invoice_report_*.txt (detailed report)
echo ============================================================
echo.

pause
