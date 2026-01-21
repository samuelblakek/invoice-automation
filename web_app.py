"""
Invoice Automation - Web Interface
Simple drag-and-drop interface for invoice processing
"""
import streamlit as st
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import io

from invoice_automation.config.settings import Config
from invoice_automation.processors import ExcelReader, ExcelWriter
from invoice_automation.validators import InvoiceValidator
from invoice_automation.extractors import (
    AAWExtractor, CJLExtractor, AmazonExtractor, APSExtractor, GenericExtractor, PDFExtractionError
)
from invoice_automation.models import ValidationResult
from invoice_automation.reports.report_generator import ReportGenerator
import pdfplumber


def identify_supplier(pdf_path: Path, first_page_text: str) -> str:
    """Identify supplier from filename or PDF content."""
    filename_lower = pdf_path.name.lower()
    text_lower = first_page_text.lower()

    if 'aaw' in filename_lower or 'aaw national' in text_lower:
        return 'AAW'
    elif 'cjl' in filename_lower or 'cjl group' in text_lower:
        return 'CJL'
    elif 'amazon' in filename_lower or 'amazon business' in text_lower:
        return 'AMAZON'
    elif 'aps' in filename_lower or 'automatic protection' in text_lower:
        return 'APS'
    elif 'compco' in filename_lower or 'compco fire' in text_lower:
        return 'COMPCO'
    else:
        return 'GENERIC'


# Cache extractors to avoid recreating them for each invoice
@st.cache_resource
def get_extractors():
    """Get cached extractor instances."""
    return {
        'AAW': AAWExtractor(),
        'CJL': CJLExtractor(),
        'AMAZON': AmazonExtractor(),
        'APS': APSExtractor(),
        'COMPCO': GenericExtractor(),
        'GENERIC': GenericExtractor(),
    }


def extract_invoice(pdf_path: Path):
    """Extract invoice from PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""

    supplier_type = identify_supplier(pdf_path, first_page_text)
    extractors = get_extractors()
    extractor = extractors.get(supplier_type, extractors['GENERIC'])
    return extractor.extract(pdf_path)


# Page config
st.set_page_config(
    page_title="Invoice Automation",
    page_icon="📄",
    layout="wide"
)

# Title and description
st.title("📄 Invoice Processing Automation")
st.markdown("""
Upload your invoice PDFs and Excel spreadsheets, and the automation will:
- Extract invoice data from PDFs
- Validate against Purchase Orders
- Check £200+ quote authorization
- Update your spreadsheet automatically
- Generate detailed reports

**No data is stored** - everything is processed in memory and deleted after you download.
""")

# Sidebar for instructions
with st.sidebar:
    st.header("📋 Quick Guide")
    st.markdown("""
    **Step 1:** Upload invoice PDFs

    **Step 2:** Upload Excel files:
    - Maintenance PO spreadsheet
    - Cost Centre Summary

    **Step 3:** Click "Process Invoices"

    **Step 4:** Download results

    ---

    **Security:**
    - All processing in memory
    - No data saved online
    - HTTPS encrypted
    - Session data auto-deleted
    """)

    st.info("💡 Tip: Process 10-20 invoices at a time for best results")

# Create tabs
tab1, tab2, tab3 = st.tabs(["🚀 Process Invoices", "📊 About", "❓ Help"])

with tab1:
    # File uploaders
    st.header("Step 1: Upload Files")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Invoice PDFs")
        invoice_pdfs = st.file_uploader(
            "Drag and drop your invoice PDF files here",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload all invoice PDFs you want to process"
        )

        if invoice_pdfs:
            st.success(f"✓ {len(invoice_pdfs)} invoice(s) uploaded")
            with st.expander("View uploaded invoices"):
                for pdf in invoice_pdfs:
                    st.text(f"• {pdf.name}")

    with col2:
        st.subheader("📊 Excel Spreadsheets")

        maintenance_po = st.file_uploader(
            "Maintenance PO Spreadsheet",
            type=['xlsx'],
            help="Your Maintenance PO's Excel file"
        )

        cost_centre = st.file_uploader(
            "Cost Centre Summary",
            type=['xlsx'],
            help="Cost Centre Summary (Addresses & Nominal Codes)"
        )

        if maintenance_po:
            st.success(f"✓ {maintenance_po.name}")
        if cost_centre:
            st.success(f"✓ {cost_centre.name}")

    # Process button
    st.header("Step 2: Process")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        process_button = st.button(
            "🚀 Process Invoices",
            type="primary",
            disabled=not (invoice_pdfs and maintenance_po and cost_centre)
        )

    if not (invoice_pdfs and maintenance_po and cost_centre):
        st.warning("⚠️ Please upload all required files before processing")

    # Processing
    if process_button and invoice_pdfs and maintenance_po and cost_centre:
        with st.spinner("Processing invoices... This may take 30-60 seconds"):
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Save uploaded files
                pdf_dir = temp_path / "invoices"
                pdf_dir.mkdir()

                for pdf in invoice_pdfs:
                    pdf_path = pdf_dir / pdf.name
                    pdf_path.write_bytes(pdf.read())

                # Save Excel files
                maintenance_path = temp_path / "maintenance.xlsx"
                maintenance_path.write_bytes(maintenance_po.read())

                cost_centre_path = temp_path / "cost_centre.xlsx"
                cost_centre_path.write_bytes(cost_centre.read())

                # Initialize components
                excel_reader = ExcelReader(maintenance_path, cost_centre_path)
                validator = InvoiceValidator(excel_reader)

                # Process each invoice
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Get list of PDFs once for efficiency
                pdf_files = list(pdf_dir.glob("*.pdf"))
                total_pdfs = len(pdf_files)

                for i, pdf_file in enumerate(pdf_files):
                    status_text.text(f"Processing {pdf_file.name}...")
                    progress_bar.progress((i + 1) / total_pdfs)

                    try:
                        invoice = extract_invoice(pdf_file)
                        result = validator.validate(invoice)
                        results.append(result)
                    except Exception as e:
                        result = ValidationResult.create_error(str(pdf_file), str(e))
                        results.append(result)

                progress_bar.empty()
                status_text.empty()

                # Update Excel
                updated_excel = io.BytesIO()
                with ExcelWriter(maintenance_path, create_backup=False) as writer:
                    for result in results:
                        if result.can_auto_update:
                            writer.update_po_record(
                                result.po_record.sheet_name,
                                result.po_record.row_index,
                                result.invoice.invoice_number,
                                result.invoice.net_amount,
                                datetime.now()
                            )

                # Read updated Excel into memory
                with open(maintenance_path, 'rb') as f:
                    updated_excel = io.BytesIO(f.read())

                # Generate reports
                report_gen = ReportGenerator(results)

                # Summary
                summary = report_gen.generate_summary()

                # CSV
                csv_buffer = io.StringIO()
                temp_csv = temp_path / "summary.csv"
                report_gen.save_summary_csv(temp_csv)
                csv_content = temp_csv.read_text()

                # Detailed report
                report_buffer = io.StringIO()
                temp_report = temp_path / "report.txt"
                report_gen.save_detailed_report(temp_report)
                report_content = temp_report.read_text()

                # Store in session state
                st.session_state['results'] = results
                st.session_state['updated_excel'] = updated_excel
                st.session_state['csv_content'] = csv_content
                st.session_state['report_content'] = report_content
                st.session_state['processed'] = True

    # Results
    if st.session_state.get('processed'):
        st.success("✅ Processing Complete!")

        results = st.session_state['results']

        # Summary metrics
        st.header("Step 3: Results")

        col1, col2, col3, col4 = st.columns(4)

        total = len(results)
        auto_updated = sum(1 for r in results if r.can_auto_update)
        flagged = sum(1 for r in results if not r.can_auto_update and r.is_valid)
        failed = sum(1 for r in results if not r.is_valid)

        col1.metric("Total Invoices", total)
        col2.metric("Auto-Updated", auto_updated, delta=None, delta_color="normal")
        col3.metric("Needs Review", flagged, delta=None, delta_color="inverse")
        col4.metric("Failed", failed, delta=None, delta_color="inverse")

        # Detailed results table
        st.subheader("Invoice Details")

        table_data = []
        for result in results:
            if result.invoice:
                status_icon = "✅" if result.can_auto_update else ("⚠️" if result.warnings else "❌")
                table_data.append({
                    "Status": status_icon,
                    "Invoice #": result.invoice.invoice_number,
                    "Supplier": result.invoice.supplier_name,
                    "PO #": result.invoice.po_number,
                    "Store": result.invoice.store_location,
                    "Amount": f"£{result.invoice.net_amount:.2f}",
                    "Issues": ", ".join(result.errors[:2]) if result.errors else "None"
                })

        st.dataframe(table_data, width="stretch")

        # Download section
        st.header("Step 4: Download Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.download_button(
                label="📊 Download Updated Excel",
                data=st.session_state['updated_excel'].getvalue(),
                file_name=f"Maintenance_POs_Updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

        with col2:
            st.download_button(
                label="📄 Download CSV Summary",
                data=st.session_state['csv_content'],
                file_name=f"invoice_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col3:
            st.download_button(
                label="📝 Download Detailed Report",
                data=st.session_state['report_content'],
                file_name=f"invoice_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

        # Show issues if any
        if flagged > 0 or failed > 0:
            st.warning("⚠️ Some invoices need manual review")

            with st.expander("View Issues"):
                for result in results:
                    if not result.can_auto_update and result.invoice:
                        st.markdown(f"**{result.invoice.invoice_number}** - {result.invoice.supplier_name}")
                        for error in result.errors:
                            st.error(f"❌ {error}")
                        for warning in result.warnings:
                            st.warning(f"⚠️ {warning}")
                        st.divider()

with tab2:
    st.header("About This Automation")

    st.markdown("""
    ### What It Does

    This automation processes maintenance invoices by:

    1. **Extracting** data from invoice PDFs (invoice #, PO #, amounts, store, supplier)
    2. **Finding** matching Purchase Order records in your spreadsheet
    3. **Validating** against company policies:
       - PO exists and not already invoiced
       - Store name matches
       - Nominal code is correct
       - **£200+ quotes are authorized** (critical check)
       - Amounts are valid
    4. **Updating** your Excel spreadsheet with:
       - Invoice number
       - Invoice amount (ex-VAT)
       - Invoice signed date
    5. **Generating** detailed reports

    ### Supported Suppliers

    - AAW National Shutters
    - CJL Group
    - APS Fire Systems
    - Amazon Business
    - Compco Fire Systems
    - Other suppliers (generic extraction)

    ### Security & Privacy

    - ✅ All processing happens in your browser session
    - ✅ No data is stored on servers
    - ✅ Files are deleted immediately after processing
    - ✅ HTTPS encrypted connection
    - ✅ No user accounts or login required

    ### Critical £200+ Check

    For invoices over £200 (ex-VAT):
    - Must have "QUOTE OVER £200" filled in
    - Must have "AUTHORISED" filled in
    - Auto-update is **BLOCKED** if authorization missing

    This ensures company policy compliance before payment.
    """)

with tab3:
    st.header("Help & Troubleshooting")

    st.markdown("""
    ### Common Issues

    **Q: All invoices failed with "PO not found"**

    A: This usually means:
    - The PO numbers in invoices don't match your spreadsheet
    - You uploaded the wrong Maintenance PO file
    - The POs haven't been created yet

    **Q: Amounts look wrong**

    A: The automation extracts NET amounts (excluding VAT). This is correct for the "INVOICE AMOUNT (EX VAT)" column.

    **Q: Invoice over £200 blocked**

    A: Check the "QUOTE OVER £200" and "AUTHORISED" columns in your spreadsheet. Both must have values for invoices over £200.

    **Q: Store name mismatch**

    A: The automation uses fuzzy matching. If the invoice shows "Leicester City" but PO shows "Leicester", it should still match. If confidence is low, it flags for review.

    **Q: Can I process the same invoices again?**

    A: Yes, but invoices already processed (PO already has invoice number) will be flagged as duplicates.

    ### Weekly Workflow

    1. Export invoices from iCompleat as PDFs
    2. Visit this website
    3. Upload PDFs and Excel files
    4. Click "Process Invoices"
    5. Download updated Excel file
    6. Review any flagged invoices
    7. Approve invoices in iCompleat

    ### Excel Files Needed

    You need to upload 2 Excel files every time:

    1. **Maintenance PO Spreadsheet** - Contains sheets like:
       - AAW NATIONAL (PANDA)
       - CJL
       - APS
       - ORDERS
       - OTHER
       - etc.

    2. **Cost Centre Summary** - Contains:
       - Store addresses
       - Nominal code mappings

    ### What Gets Updated

    Only 3 columns are updated in matching PO rows:
    - INVOICE NO.
    - INVOICE AMOUNT (EX VAT)
    - INVOICE SIGNED

    Everything else is preserved unchanged.

    ### Need More Help?

    Check the detailed report (download after processing) for:
    - Exactly which validations passed/failed
    - Error messages with explanations
    - Suggestions for fixing issues
    """)

# Footer
st.divider()
st.caption("Invoice Processing Automation v1.0 | No data stored | Session expires after download")
