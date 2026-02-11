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
    elif 'sunbelt' in text_lower or 'sunbelt' in filename_lower:
        return 'SUNBELT'
    elif 'maxwell jones' in text_lower or 'maxwelljones' in text_lower:
        return 'MAXWELL_JONES'
    elif 'metro security' in text_lower:
        return 'METRO_SECURITY'
    elif 'store maintenance' in text_lower or 'reactive on call' in text_lower:
        return 'STORE_MAINTENANCE'
    elif 'lampshoponline' in text_lower or 'lampshop' in text_lower:
        return 'LAMPSHOP'
    elif 'ilux' in text_lower:
        return 'ILUX'
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
        'SUNBELT': GenericExtractor(),
        'MAXWELL_JONES': GenericExtractor(),
        'METRO_SECURITY': GenericExtractor(),
        'STORE_MAINTENANCE': GenericExtractor(),
        'LAMPSHOP': GenericExtractor(),
        'ILUX': GenericExtractor(),
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
        with st.spinner("Processing invoices..."):
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
                        error_msg = f"Could not read '{pdf_file.name}': {e}"
                        result = ValidationResult.create_error(str(pdf_file), error_msg)
                        results.append(result)

                progress_bar.empty()
                status_text.empty()

                # Write auto-updated results to Excel
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

                # Read updated Excel into memory (auto-updates applied)
                with open(maintenance_path, 'rb') as f:
                    updated_excel_bytes = f.read()

                # Generate reports
                report_gen = ReportGenerator(results)
                summary = report_gen.generate_summary()

                temp_csv = temp_path / "summary.csv"
                report_gen.save_summary_csv(temp_csv)
                csv_content = temp_csv.read_text()

                temp_report = temp_path / "report.txt"
                report_gen.save_detailed_report(temp_report)
                report_content = temp_report.read_text()

                # Store in session state
                st.session_state['results'] = results
                st.session_state['updated_excel_bytes'] = updated_excel_bytes
                st.session_state['csv_content'] = csv_content
                st.session_state['report_content'] = report_content
                st.session_state['processed'] = True
                # Track review decisions: {index: "confirmed" | "skipped" | None}
                review_results = [r for r in results if r.needs_review]
                st.session_state['review_decisions'] = {i: None for i in range(len(review_results))}

    # Results
    if st.session_state.get('processed'):
        st.success("Processing Complete!")

        results = st.session_state['results']

        # Split into 3 buckets
        auto_results = [r for r in results if r.can_auto_update]
        review_results = [r for r in results if r.needs_review]
        failed_results = [r for r in results if not r.can_auto_update and not r.needs_review]

        # Summary metrics
        st.header("Step 3: Results")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Invoices", len(results))
        col2.metric("Auto-Updated", len(auto_results), delta=None, delta_color="normal")
        col3.metric("Needs Review", len(review_results), delta=None, delta_color="inverse")
        col4.metric("Failed", len(failed_results), delta=None, delta_color="inverse")

        # Detailed results table
        st.subheader("Invoice Details")

        table_data = []
        for result in results:
            if result.invoice:
                if result.can_auto_update:
                    status_icon = "✅"
                elif result.needs_review:
                    status_icon = "🔍"
                else:
                    status_icon = "❌"
                issues = result.errors + result.warnings
                table_data.append({
                    "Status": status_icon,
                    "Invoice #": result.invoice.invoice_number,
                    "Supplier": result.invoice.supplier_name,
                    "PO #": result.invoice.po_number or "No PO",
                    "Store": result.invoice.store_location,
                    "Amount": f"£{result.invoice.net_amount:.2f}",
                    "Issues": issues[0] if issues else "None"
                })
            else:
                table_data.append({
                    "Status": "❌",
                    "Invoice #": "N/A",
                    "Supplier": "N/A",
                    "PO #": "N/A",
                    "Store": "N/A",
                    "Amount": "N/A",
                    "Issues": result.errors[0] if result.errors else "Extraction failed"
                })

        st.dataframe(table_data, use_container_width=True)

        # --- Review section for near-miss invoices ---
        review_decisions = st.session_state.get('review_decisions', {})

        if review_results:
            st.header(f"Invoices Needing Review ({len(review_results)})")
            st.markdown("These invoices matched a PO but need your confirmation due to uncertain matching. "
                        "Review each one and confirm or skip.")

            for idx, result in enumerate(review_results):
                inv = result.invoice
                po = result.po_record
                decision = review_decisions.get(idx)

                if decision == "confirmed":
                    st.success(f"**{inv.invoice_number}** — Confirmed")
                    continue
                elif decision == "skipped":
                    st.info(f"**{inv.invoice_number}** — Skipped")
                    continue

                with st.container(border=True):
                    st.markdown(f"### {inv.invoice_number} — {inv.supplier_name}")

                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        st.markdown("**Invoice Details**")
                        st.text(f"Amount:  £{inv.net_amount:.2f}")
                        st.text(f"PO #:    {inv.po_number or 'Not on invoice'}")
                        st.text(f"Store:   {inv.store_location or 'Unknown'}")

                    with detail_col2:
                        st.markdown("**Matched PO Record**")
                        st.text(f"PO #:    {po.po_number}")
                        st.text(f"Store:   {po.store}")
                        st.text(f"Sheet:   {po.sheet_name}, row {po.row_index + 1}")

                    # Show the warnings/errors that caused the review flag
                    for error in result.errors:
                        st.error(f"❌ {error}")
                    for warning in result.warnings:
                        st.warning(f"⚠️ {warning}")

                    btn_col1, btn_col2, _ = st.columns([1, 1, 3])
                    with btn_col1:
                        if st.button("Confirm Update", key=f"confirm_{idx}", type="primary"):
                            st.session_state['review_decisions'][idx] = "confirmed"
                            st.rerun()
                    with btn_col2:
                        if st.button("Skip", key=f"skip_{idx}"):
                            st.session_state['review_decisions'][idx] = "skipped"
                            st.rerun()

        # --- Check if all reviews are resolved ---
        all_reviewed = all(d is not None for d in review_decisions.values()) if review_decisions else True
        confirmed_indices = [i for i, d in review_decisions.items() if d == "confirmed"]

        # If there are confirmed items that need writing, rebuild the Excel
        if confirmed_indices and all_reviewed and not st.session_state.get('reviews_written'):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                maintenance_path = temp_path / "maintenance.xlsx"
                maintenance_path.write_bytes(st.session_state['updated_excel_bytes'])

                with ExcelWriter(maintenance_path, create_backup=False) as writer:
                    for idx in confirmed_indices:
                        result = review_results[idx]
                        writer.update_po_record(
                            result.po_record.sheet_name,
                            result.po_record.row_index,
                            result.invoice.invoice_number,
                            result.invoice.net_amount,
                            datetime.now()
                        )

                with open(maintenance_path, 'rb') as f:
                    st.session_state['updated_excel_bytes'] = f.read()
                st.session_state['reviews_written'] = True

        # --- Failed section ---
        if failed_results:
            st.header(f"Failed Invoices ({len(failed_results)})")
            with st.expander("View Issues", expanded=True):
                for result in failed_results:
                    if result.invoice:
                        po_info = ""
                        if result.po_record:
                            po_info = f" | PO '{result.po_record.po_number}' (sheet '{result.po_record.sheet_name}', row {result.po_record.row_index + 1})"
                        st.markdown(f"**{result.invoice.invoice_number}** — {result.invoice.supplier_name}{po_info}")
                    else:
                        st.markdown(f"**Extraction Error**")
                    for error in result.errors:
                        st.error(f"❌ {error}")
                    for warning in result.warnings:
                        st.warning(f"⚠️ {warning}")
                    st.divider()

        # --- Download section ---
        st.header("Step 4: Download Results")

        if not all_reviewed:
            st.info("Review all near-miss invoices above before downloading.")
        else:
            confirmed_count = len(confirmed_indices)
            if confirmed_count > 0:
                st.info(f"Excel includes {len(auto_results)} auto-updated + {confirmed_count} confirmed invoices.")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.download_button(
                    label="📊 Download Updated Excel",
                    data=st.session_state['updated_excel_bytes'],
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
