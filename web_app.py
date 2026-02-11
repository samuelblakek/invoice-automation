"""
Invoice Automation - Web Interface
Simple drag-and-drop interface for invoice processing
"""
import json
import streamlit as st
import tempfile
from pathlib import Path
from datetime import datetime

from invoice_automation.processors import ExcelReader, ExcelWriter
from invoice_automation.validators import InvoiceValidator
from invoice_automation.extractors import (
    AAWExtractor, CJLExtractor, AmazonExtractor, APSExtractor, GenericExtractor, PDFExtractionError
)
from invoice_automation.models import ValidationResult
from invoice_automation.reports.report_generator import ReportGenerator
import pdfplumber


# ---------------------------------------------------------------------------
# Global CSS -- Outfit font, dark slate/navy palette, glassmorphism + grain
# ---------------------------------------------------------------------------
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

/* ---------- Font override ---------- */
html, body, [class*="css"], .stMarkdown, .stText,
.stSelectbox, .stMultiSelect, .stRadio, .stCheckbox,
h1, h2, h3, h4, h5, h6, p, div, label, input, textarea, button, a {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
/* Apply Outfit to spans, but NOT inside expander summaries where icon fonts live */
span {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
/* Restore icon font for expander toggle arrows -- higher specificity beats the span rule */
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] + div span,
details summary span {
    font-family: 'Material Symbols Rounded', sans-serif !important;
}
/* Also restore for any standalone icon use */
.material-symbols-rounded,
[data-baseweb="icon"],
[data-baseweb="icon"] * {
    font-family: 'Material Symbols Rounded', sans-serif !important;
}

/* ---------- Colour tokens (dark slate / navy) ---------- */
:root {
    --bg-primary:    #0F1923;
    --bg-card:       rgba(255, 255, 255, 0.05);
    --bg-card-hover: rgba(255, 255, 255, 0.08);
    --bg-elevated:   rgba(255, 255, 255, 0.10);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: rgba(255, 255, 255, 0.15);
    --text-primary:  #E2E8F0;
    --text-secondary:#94A3B8;
    --text-muted:    #64748B;
    --accent:        #E2E8F0;
    --green:         #34D399;
    --green-bg:      rgba(52, 211, 153, 0.10);
    --green-border:  rgba(52, 211, 153, 0.25);
    --amber:         #FBBF24;
    --amber-bg:      rgba(251, 191, 36, 0.10);
    --amber-border:  rgba(251, 191, 36, 0.25);
    --red:           #F87171;
    --red-bg:        rgba(248, 113, 113, 0.10);
    --red-border:    rgba(248, 113, 113, 0.25);
}

/* ---------- Hide Streamlit branding ---------- */
#MainMenu, footer { visibility: hidden; }
/* Hide deploy button */
[data-testid="stAppDeployButton"] { display: none; }
/* Make header transparent so sidebar toggle remains accessible */
header[data-testid="stHeader"] {
    background: transparent !important;
}
/* Restore icon font for sidebar collapse/expand buttons */
header[data-testid="stHeader"] button span,
[data-testid="stSidebarCollapsedControl"] span,
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="stBaseButton-headerNoPadding"] span {
    font-family: 'Material Symbols Rounded', sans-serif !important;
}

/* ---------- Body background (layered gradients with colour glow) ---------- */
.stApp {
    background:
        radial-gradient(ellipse at 30% 20%, rgba(56, 189, 248, 0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 60%, rgba(139, 92, 246, 0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 0%, #1A2A3A 0%, #0F1923 60%) !important;
}

/* ---------- Noise / grain overlay ---------- */
.stApp::after {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 999;
    opacity: 0.04;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='a' x='0' y='0'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.75' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23a)'/%3E%3C/svg%3E");
    background-size: 200px;
}

/* ---------- Sidebar (frosted glass) ---------- */
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}

/* ---------- Invoice card (solid glass-like, no backdrop-filter to avoid scroll artefacts) ---------- */
.inv-card {
    background: rgba(22, 34, 49, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 3px solid var(--card-accent, rgba(255, 255, 255, 0.08));
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.inv-card:hover {
    background: rgba(26, 40, 56, 0.9);
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
.inv-card .inv-num {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-primary);
}
.inv-card .inv-supplier {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 0.15rem;
}
.inv-card .inv-amount {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 0.4rem;
}
.inv-card .inv-detail {
    color: var(--text-muted);
    font-size: 0.8rem;
    margin-top: 0.2rem;
}
.inv-card .inv-error {
    color: var(--red);
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.inv-card .inv-warning {
    color: var(--amber);
    font-size: 0.78rem;
    margin-top: 0.4rem;
    padding-left: 1.2em;
    text-indent: -1.2em;
    line-height: 1.4;
}

/* ---------- Column header pills ---------- */
.col-header {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    margin-bottom: 1rem;
    border: 1px solid;
}
.col-header-green  { background: var(--green-bg);  color: var(--green);  border-color: var(--green-border); }
.col-header-amber  { background: var(--amber-bg);  color: var(--amber);  border-color: var(--amber-border); }
.col-header-red    { background: var(--red-bg);    color: var(--red);    border-color: var(--red-border); }

/* ---------- Compact inline metrics ---------- */
.inline-metrics {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-subtle);
}
.inline-metric { font-size: 0.875rem; color: var(--text-secondary); }
.inline-metric strong {
    color: var(--text-primary);
    font-size: 1rem;
    font-weight: 700;
    margin-right: 0.3rem;
}

/* ---------- Section divider ---------- */
.section-divider {
    border: none;
    border-top: 1px solid var(--border-subtle);
    margin: 2rem 0;
}

/* ---------- Button overrides ---------- */
/* Primary buttons: warm neutral (white bg, dark text) */
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    background-color: #E2E8F0 !important;
    border: 1px solid #E2E8F0 !important;
    color: #0F1923 !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s ease !important;
}
button[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
    background-color: #FFFFFF !important;
    border-color: #FFFFFF !important;
    color: #000000 !important;
}

/* Secondary buttons: ghost style */
button[data-testid="stBaseButton-secondary"],
button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid var(--border-medium) !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    transition: all 0.15s ease !important;
}
button[data-testid="stBaseButton-secondary"]:hover,
button[kind="secondary"]:hover {
    border-color: var(--text-muted) !important;
    color: var(--text-primary) !important;
    background-color: var(--bg-elevated) !important;
}

/* Reset button -- red destructive style (targeted via widget key) */
.st-key-reset_app button {
    background-color: transparent !important;
    border: 1px solid var(--red-border) !important;
    color: var(--red) !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    transition: all 0.15s ease !important;
}
.st-key-reset_app button:hover {
    background-color: var(--red-bg) !important;
    border-color: var(--red) !important;
    color: var(--red) !important;
}

/* Download buttons -- normalise height */
[data-testid="stDownloadButton"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    min-height: 2.8rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stDownloadButton"] button p {
    margin: 0 !important;
    line-height: 1.3 !important;
    font-size: 0.82rem !important;
}
</style>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def inv_card_html(inv, po=None, extra="", accent="var(--border-subtle)"):
    """Generate HTML for an invoice card."""
    po_line = f'<div class="inv-detail">PO: {po.po_number}  |  {po.store}</div>' if po else ""
    return f'''<div class="inv-card" style="--card-accent:{accent}">
        <div class="inv-num">{inv.invoice_number}</div>
        <div class="inv-supplier">{inv.supplier_name}</div>
        <div class="inv-amount">&pound;{inv.net_amount:.2f}</div>
        <div class="inv-detail">Store: {inv.store_location}</div>
        {po_line}{extra}
    </div>'''


def lookup_nominal_code(supplier_name: str, rows: list[dict],
                        invoice_text: str = "") -> str:
    """Find nominal code for supplier, using invoice text to disambiguate
    when a supplier has multiple codes for different work types.

    The Supplier field in the mapping may contain a work-type suffix after
    a dash, e.g. "Metro Security (UK) Limited (MetSafe) - safe installation".
    The base name is the part before the first " - ".

    Steps:
    1. Find all rows whose base supplier name matches the invoice supplier.
    2. If only one match, return that code.
    3. If multiple matches (different work types), score each by how many
       words from the work-type description appear in the invoice text.
       Return the best-scoring code.
    4. If no match on base name, try first-word fallback.
    """
    if not supplier_name or not rows:
        return ""

    supplier_lower = supplier_name.lower()
    invoice_lower = invoice_text.lower() if invoice_text else ""

    def base_name(entry: str) -> str:
        return entry.split(" - ")[0].strip()

    def work_desc(entry: str) -> str:
        parts = entry.split(" - ", 1)
        return parts[1].strip() if len(parts) > 1 else ""

    def name_matches(entry_base: str, supplier: str) -> bool:
        if entry_base in supplier or supplier in entry_base:
            return True
        # Also try with spaces stripped (e.g. "LampShopOnline" vs "lamp shop online")
        entry_nospace = entry_base.replace(" ", "")
        supplier_nospace = supplier.replace(" ", "")
        return entry_nospace in supplier_nospace or supplier_nospace in entry_nospace

    # Collect all matching rows
    matches = []
    for row in rows:
        entry = str(row.get("Supplier", "")).strip()
        code = str(row.get("Nominal Code", "")).strip()
        if not entry or not code:
            continue
        entry_lower = entry.lower()
        entry_base = base_name(entry_lower)
        if name_matches(entry_base, supplier_lower):
            matches.append((entry_lower, code, work_desc(entry_lower)))

    if not matches:
        # First-word fallback
        first_word = supplier_lower.split()[0] if supplier_lower.split() else ""
        if first_word and len(first_word) >= 3:
            for row in rows:
                entry = str(row.get("Supplier", "")).strip()
                code = str(row.get("Nominal Code", "")).strip()
                if not entry or not code:
                    continue
                entry_base = base_name(entry.lower())
                if first_word in entry_base or entry_base.startswith(first_word):
                    matches.append((entry.lower(), code, work_desc(entry.lower())))
        if not matches:
            return ""

    # Single match  - return directly
    if len(matches) == 1:
        return matches[0][1]

    # Multiple matches  - score by work description overlap with invoice text
    if not invoice_lower:
        return matches[0][1]  # No invoice text to compare, return first

    best_code = matches[0][1]
    best_score = -1
    for _entry, code, desc in matches:
        if not desc:
            continue
        words = [w for w in desc.split() if len(w) >= 3]
        score = sum(1 for w in words if w in invoice_lower)
        if score > best_score:
            best_score = score
            best_code = code

    return best_code


NOMINAL_CODES_PATH = Path(__file__).parent / "data" / "nominal_codes.json"


def load_nominal_codes_from_disk() -> list[dict]:
    """Load supplier→nominal code mapping from JSON file."""
    if NOMINAL_CODES_PATH.exists():
        with open(NOMINAL_CODES_PATH) as f:
            return json.load(f)
    return []


def save_nominal_codes_to_disk(rows: list[dict]):
    """Persist supplier→nominal code mapping to JSON file."""
    NOMINAL_CODES_PATH.parent.mkdir(exist_ok=True)
    with open(NOMINAL_CODES_PATH, "w") as f:
        json.dump(rows, f, indent=2)


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


# ---------------------------------------------------------------------------
# Page config + CSS injection
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Invoice Automation",
    page_icon="📄",
    layout="wide"
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar -- file uploaders, process button, about/help
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Upload Files")

    # Counter used to generate unique widget keys -- incrementing it forces
    # Streamlit to recreate the file uploaders, clearing uploaded files.
    upload_gen = st.session_state.get('upload_gen', 0)

    invoice_pdfs = st.file_uploader(
        "Invoice PDFs",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload all invoice PDFs you want to process",
        key=f"pdf_uploader_{upload_gen}"
    )

    maintenance_po = st.file_uploader(
        "Maintenance PO Spreadsheet",
        type=['xlsx'],
        help="Your Maintenance PO's Excel file",
        key=f"maintenance_uploader_{upload_gen}"
    )

    # --- Nominal code mapping (always visible, backed by JSON file) ---
    if 'nominal_mapping_rows' not in st.session_state:
        st.session_state['nominal_mapping_rows'] = load_nominal_codes_from_disk()

    nom_gen = st.session_state.get('nom_input_gen', 0)

    with st.expander("Supplier Nominal Codes"):
        # Show feedback from previous action
        nom_msg = st.session_state.pop('nom_feedback', None)
        if nom_msg:
            st.success(nom_msg)

        rows = st.session_state['nominal_mapping_rows']
        scroll_to_bottom = st.session_state.pop('nom_scroll_bottom', False)
        if rows:
            list_html = "".join(
                f'<div style="padding:0.3rem 0;border-bottom:1px solid var(--border-subtle)">'
                f'<div style="color:var(--text-primary);font-size:0.82rem">{r["Supplier"]}</div>'
                f'<div style="color:var(--text-muted);font-size:0.75rem">{r["Nominal Code"]}</div>'
                f'</div>'
                for r in rows
            )
            scroll_js = ""
            if scroll_to_bottom:
                scroll_js = '<script>var el=document.getElementById("nom-list");if(el)el.scrollTop=el.scrollHeight;</script>'
            st.markdown(
                f'<div id="nom-list" style="max-height:260px;overflow-y:auto;border:1px solid var(--border-medium);border-radius:6px;padding:0.4rem 0.6rem;margin-bottom:0.75rem">{list_html}</div>{scroll_js}',
                unsafe_allow_html=True
            )
        else:
            st.caption("No mappings configured")

        # Add new entry
        new_supplier = st.text_input("Supplier", key=f"new_nom_supplier_{nom_gen}",
                                     placeholder="e.g. Lamp Shop Online")
        new_code = st.text_input("Nominal Code", key=f"new_nom_code_{nom_gen}",
                                 placeholder="e.g. 7820 Stores Repairs")
        if st.button("Add", use_container_width=True, key="add_nominal",
                      disabled=not (new_supplier and new_code)):
            added_name = new_supplier.strip()
            st.session_state['nominal_mapping_rows'].append(
                {"Supplier": added_name, "Nominal Code": new_code.strip()}
            )
            save_nominal_codes_to_disk(st.session_state['nominal_mapping_rows'])
            st.session_state['nom_input_gen'] = nom_gen + 1
            st.session_state['nom_feedback'] = f"Added {added_name}"
            st.session_state['nom_scroll_bottom'] = True
            st.rerun()

        # Delete entry
        if rows:
            del_options = [r["Supplier"] for r in rows]
            del_choice = st.selectbox("Remove supplier", del_options,
                                      index=None, placeholder="Select to remove...",
                                      key=f"del_nominal_select_{nom_gen}")
            if del_choice and st.button("Remove", use_container_width=True,
                                         key="del_nominal"):
                st.session_state['nominal_mapping_rows'] = [
                    r for r in rows if r["Supplier"] != del_choice
                ]
                save_nominal_codes_to_disk(st.session_state['nominal_mapping_rows'])
                st.session_state['nom_input_gen'] = nom_gen + 1
                st.session_state['nom_feedback'] = f"Removed {del_choice}"
                st.rerun()

    st.markdown("")
    all_files_uploaded = bool(invoice_pdfs and maintenance_po)
    process_button = st.button(
        "Process Invoices",
        type="primary",
        disabled=not all_files_uploaded,
        use_container_width=True
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    with st.expander("About"):
        st.markdown("""
Extracts invoice data from PDFs, matches against Purchase Orders, assigns
nominal codes, and updates the Maintenance PO spreadsheet automatically.

**What it does:**
1. Extract data from invoice PDFs (supplier, PO, amounts, store, description)
2. Match to Purchase Order records (exact, invoice number search, or fuzzy)
3. Look up the correct nominal code from the supplier mapping
4. Validate amounts and flag anything that needs review
5. Update your Excel spreadsheet with invoice number, amount, date, and nominal code
6. Generate summary reports

**Nominal codes:** Managed in the Supplier Nominal Codes section in the sidebar. Codes are saved locally and persist between sessions. Suppliers with multiple work types are matched automatically based on invoice content.

**Supported suppliers:** Lamp Shop Online, CJL, APS, Metro Security, Compco, Aura, Sunbelt, and others via generic extraction.

**Security:** All processing happens locally in your browser session. No data is sent to external servers.
        """)

    with st.expander("Help"):
        st.markdown("""
**Common issues:**
- **PO not found** - Wrong Excel file, or POs not yet created
- **Amounts wrong** - Amounts are NET (ex-VAT), which is correct
- **Over 200 warning** - Check QUOTE OVER 200 and AUTHORISED columns
- **Store mismatch** - Fuzzy matching is used; low confidence flags for review
- **No nominal code** - Supplier not in the mapping table. Add them via the Supplier Nominal Codes section in the sidebar

**Nominal code tips:**
- For suppliers with one type of work, just add the supplier name and code
- For suppliers with multiple work types, add separate entries with a description after a dash (e.g. "Metro Security - Safe Installation" and "Metro Security - Safe Removal")
- The app matches invoice text against the description to pick the right code

**Weekly workflow:**
1. Export invoices from iCompleat as PDFs
2. Upload PDFs and the Maintenance PO spreadsheet
3. Click Process Invoices
4. Review any flagged invoices
5. Download the updated Excel
6. Approve in iCompleat
        """)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    if st.button("Reset App", key="reset_app", use_container_width=True):
        next_gen = st.session_state.get('upload_gen', 0) + 1
        st.session_state.clear()
        st.session_state['upload_gen'] = next_gen
        st.session_state['nominal_mapping_rows'] = load_nominal_codes_from_disk()
        st.rerun()


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
import base64
_logo_path = Path(__file__).parent / "assets" / "menkind-logo.jpg"
if _logo_path.exists():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
    st.markdown(
        f'<div style="display:flex;flex-direction:column;align-items:flex-start;gap:0.5rem;margin-bottom:0.25rem">'
        f'<img src="data:image/jpeg;base64,{_logo_b64}" '
        f'style="width:52px;height:52px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.3)" />'
        f'</div>',
        unsafe_allow_html=True
    )
st.markdown("## Menkind Maintenance PO Processing")

# Empty state -- no files uploaded
if not all_files_uploaded and not st.session_state.get('processed'):
    st.markdown("Upload files in the sidebar to get started.")

# Files uploaded but not yet processed
elif all_files_uploaded and not st.session_state.get('processed') and not process_button:
    st.markdown("Files uploaded. Click **Process Invoices** in the sidebar.")

# ---------------------------------------------------------------------------
# Processing pipeline (preserved exactly from original)
# ---------------------------------------------------------------------------
if process_button and all_files_uploaded:
    with st.spinner("Processing invoices..."):
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

            # Initialize components
            excel_reader = ExcelReader(maintenance_path)
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

            # Look up nominal codes and warn on misses
            nominal_rows = st.session_state.get('nominal_mapping_rows', [])
            for result in results:
                if result.invoice:
                    inv = result.invoice
                    nom_code = lookup_nominal_code(
                        inv.supplier_name, nominal_rows,
                        invoice_text=f"{inv.description} {inv.raw_text}"
                    )
                    result._nominal_code = nom_code
                    if not nom_code:
                        result.warnings.append(
                            f"No nominal code mapping for '{inv.supplier_name}'"
                        )

            # Write auto-updated results to Excel
            with ExcelWriter(maintenance_path, create_backup=False) as writer:
                for result in results:
                    if result.can_auto_update:
                        nom_code = getattr(result, '_nominal_code', '')
                        writer.update_po_record(
                            result.po_record.sheet_name,
                            result.po_record.row_index,
                            result.invoice.invoice_number,
                            result.invoice.net_amount,
                            datetime.now(),
                            nominal_code=nom_code
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


# ---------------------------------------------------------------------------
# Results -- three-column board layout
# ---------------------------------------------------------------------------
if st.session_state.get('processed'):
    results = st.session_state['results']

    # Split into 3 buckets
    auto_results = [r for r in results if r.can_auto_update]
    review_results = [r for r in results if r.needs_review]
    failed_results = [r for r in results if not r.can_auto_update and not r.needs_review]

    # Inline metrics
    metrics_html = f'''<div class="inline-metrics">
        <div class="inline-metric"><strong>{len(results)}</strong> total</div>
        <div class="inline-metric"><strong>{len(auto_results)}</strong> matched</div>
        <div class="inline-metric"><strong>{len(review_results)}</strong> review</div>
        <div class="inline-metric"><strong>{len(failed_results)}</strong> failed</div>
    </div>'''
    st.markdown(metrics_html, unsafe_allow_html=True)

    # Three-column board
    col_match, col_review, col_fail = st.columns(3)

    # --- Matched column ---
    with col_match:
        st.markdown(f'<div class="col-header col-header-green">Matched ({len(auto_results)})</div>', unsafe_allow_html=True)
        for r in auto_results:
            warn_html = "".join(f'<div class="inv-warning">⚠ {w}</div>' for w in r.warnings)
            st.markdown(inv_card_html(r.invoice, r.po_record, warn_html, accent="var(--green)"), unsafe_allow_html=True)

    # --- Review column ---
    with col_review:
        st.markdown(f'<div class="col-header col-header-amber">Needs Review ({len(review_results)})</div>', unsafe_allow_html=True)
        review_decisions = st.session_state.get('review_decisions', {})

        for idx, result in enumerate(review_results):
            inv = result.invoice
            po = result.po_record
            decision = review_decisions.get(idx)

            if decision == "confirmed":
                st.success(f"**{inv.invoice_number}** - Confirmed")
                continue
            elif decision == "skipped":
                st.info(f"**{inv.invoice_number}** - Skipped")
                continue

            with st.container(border=True):
                st.markdown(f"**{inv.invoice_number}**")
                st.caption(f"{inv.supplier_name}")
                st.markdown(f"**\u00a3{inv.net_amount:.2f}**")
                st.caption(f"Store: {inv.store_location}")
                if po:
                    st.caption(f"PO: {po.po_number}  |  {po.store}")

                for error in result.errors:
                    st.markdown(f"<span style='color:var(--amber);font-size:0.78rem'>⚠ {error}</span>", unsafe_allow_html=True)
                for warning in result.warnings:
                    st.markdown(f"<span style='color:var(--amber);font-size:0.78rem'>⚠ {warning}</span>", unsafe_allow_html=True)

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Confirm Update", key=f"confirm_{idx}", type="primary",
                                 use_container_width=True):
                        st.session_state['review_decisions'][idx] = "confirmed"
                        st.rerun()
                with bc2:
                    if st.button("Skip", key=f"skip_{idx}", use_container_width=True):
                        st.session_state['review_decisions'][idx] = "skipped"
                        st.rerun()

    # --- Failed column ---
    with col_fail:
        st.markdown(f'<div class="col-header col-header-red">Failed ({len(failed_results)})</div>', unsafe_allow_html=True)
        for result in failed_results:
            err_html = "".join(f'<div class="inv-error">{e}</div>' for e in result.errors)
            if result.invoice:
                st.markdown(inv_card_html(result.invoice, result.po_record, err_html, accent="var(--red)"), unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="inv-card" style="--card-accent:var(--red)">
                    <div class="inv-num">Extraction Error</div>
                    {err_html}
                </div>''', unsafe_allow_html=True)

    # --- Check if all reviews are resolved ---
    review_decisions = st.session_state.get('review_decisions', {})
    all_reviewed = all(d is not None for d in review_decisions.values()) if review_decisions else True
    confirmed_indices = [i for i, d in review_decisions.items() if d == "confirmed"]

    # If there are confirmed items that need writing, rebuild the Excel
    if confirmed_indices and all_reviewed and not st.session_state.get('reviews_written'):
        nominal_rows = st.session_state.get('nominal_mapping_rows', [])

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            maintenance_path = temp_path / "maintenance.xlsx"
            maintenance_path.write_bytes(st.session_state['updated_excel_bytes'])

            with ExcelWriter(maintenance_path, create_backup=False) as writer:
                for idx in confirmed_indices:
                    result = review_results[idx]
                    inv = result.invoice
                    nom_code = lookup_nominal_code(
                        inv.supplier_name, nominal_rows,
                        invoice_text=f"{inv.description} {inv.raw_text}"
                    )
                    writer.update_po_record(
                        result.po_record.sheet_name,
                        result.po_record.row_index,
                        result.invoice.invoice_number,
                        result.invoice.net_amount,
                        datetime.now(),
                        nominal_code=nom_code
                    )

            with open(maintenance_path, 'rb') as f:
                st.session_state['updated_excel_bytes'] = f.read()
            st.session_state['reviews_written'] = True

    # --- Download section ---
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if not all_reviewed:
        st.info("Review all near-miss invoices above before downloading.")
    else:
        confirmed_count = len(confirmed_indices)
        if confirmed_count > 0:
            st.info(f"Excel includes {len(auto_results)} auto-updated + {confirmed_count} confirmed invoices.")

        dc1, dc2, dc3 = st.columns(3)

        with dc1:
            st.download_button(
                label="Download Updated Excel",
                data=st.session_state['updated_excel_bytes'],
                file_name=f"Maintenance_POs_Updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        with dc2:
            st.download_button(
                label="Download CSV Summary",
                data=st.session_state['csv_content'],
                file_name=f"invoice_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with dc3:
            st.download_button(
                label="Download Detailed Report",
                data=st.session_state['report_content'],
                file_name=f"invoice_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
