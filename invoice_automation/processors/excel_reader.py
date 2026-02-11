"""
Excel reader for loading reference data and PO records.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from decimal import Decimal

from ..models import PORecord
from ..utils import DateParser


class ExcelReader:
    """Reader for loading data from Excel workbooks."""

    def __init__(self, maintenance_workbook_path: Path, cost_centre_path: Path):
        self.maintenance_workbook_path = Path(maintenance_workbook_path)
        self.cost_centre_path = Path(cost_centre_path)
        self.date_parser = DateParser()

    def _read_sheet_with_header_detection(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Read a sheet, auto-detecting the header row by scanning for 'PO' in any cell.

        Scans first 20 rows for the row containing 'PO' as a cell value,
        then re-reads with that row as the header. Normalizes column names.
        """
        try:
            # Read raw to find header row
            raw = pd.read_excel(
                self.maintenance_workbook_path,
                sheet_name=sheet_name,
                header=None,
                nrows=20,
                dtype=str
            )
        except Exception as e:
            print(f"Warning: Could not load sheet '{sheet_name}': {e}")
            return None

        # Find the row that contains 'PO' as a cell value
        header_row = None
        for idx, row in raw.iterrows():
            for val in row.values:
                if pd.notna(val) and str(val).strip().upper() == 'PO':
                    header_row = idx
                    break
            if header_row is not None:
                break

        if header_row is None:
            # Fallback: read with default header
            try:
                return pd.read_excel(
                    self.maintenance_workbook_path,
                    sheet_name=sheet_name,
                    dtype=str
                )
            except Exception:
                return None

        # Re-read with detected header row
        try:
            df = pd.read_excel(
                self.maintenance_workbook_path,
                sheet_name=sheet_name,
                header=header_row,
                dtype=str
            )
        except Exception as e:
            print(f"Warning: Could not re-read sheet '{sheet_name}' with header row {header_row}: {e}")
            return None

        # Normalize column names
        df.columns = [self._normalize_column_name(c) for c in df.columns]

        return df

    @staticmethod
    def _normalize_column_name(col_name) -> str:
        """Normalize a column name: strip whitespace, replace newlines, map variants."""
        if pd.isna(col_name):
            return ''
        s = str(col_name).strip()
        # Replace newlines with space, collapse whitespace
        s = ' '.join(s.split())

        # Map common variants to canonical names
        upper = s.upper()
        if upper.startswith('QUOTE OVER'):
            return 'QUOTE OVER £200'
        if upper == 'ORDER DETAILS':
            return 'ORDER DETAILS'
        if upper == 'SUPPLIER':
            return 'SUPPLIER'
        if upper == 'COMPANY NAME':
            return 'COMPANY NAME'

        return s

    def load_maintenance_sheets(self) -> Dict[str, pd.DataFrame]:
        """Load all maintenance PO sheets from the workbook."""
        sheets_to_load = [
            'AAW NATIONAL (PANDA)',
            'CJL',
            'APS',
            'ORDERS',
            'OTHER',
            'STORE MAINTENANCE',
            'AURA AC',
        ]

        sheets = {}
        for sheet_name in sheets_to_load:
            df = self._read_sheet_with_header_detection(sheet_name)
            if df is not None:
                sheets[sheet_name] = df

        return sheets

    def load_codes_sheet(self) -> pd.DataFrame:
        """Load the CODES reference sheet."""
        try:
            df = pd.read_excel(
                self.maintenance_workbook_path,
                sheet_name='CODES'
            )
            return df
        except Exception as e:
            print(f"Warning: Could not load CODES sheet: {e}")
            return pd.DataFrame()

    def load_cost_centre_summary(self) -> pd.DataFrame:
        """Load the Cost Centre Summary (store addresses)."""
        try:
            df = pd.read_excel(
                self.cost_centre_path,
                sheet_name='Cost Centre Summary SK'
            )
            return df
        except Exception as e:
            print(f"Warning: Could not load Cost Centre Summary: {e}")
            return pd.DataFrame()

    def find_po_record(self, po_number: str, sheet_name: str) -> Optional[PORecord]:
        """
        Find a PO record in a specific sheet using substring matching.

        A cell like '\\nCJL408\\n' will match PO 'CJL408' via contains match.
        """
        if not po_number or not str(po_number).strip():
            return None

        df = self._read_sheet_with_header_detection(sheet_name)
        if df is None:
            return None

        if 'PO' not in df.columns:
            return None

        po_clean = str(po_number).strip().upper()

        # Substring/contains matching: search for PO value within cell content
        df['_po_normalized'] = df['PO'].fillna('').astype(str).str.upper()
        matches = df[df['_po_normalized'].str.contains(po_clean, na=False, regex=False)]

        if matches.empty:
            df.drop('_po_normalized', axis=1, inplace=True)
            return None

        idx = matches.index[0]
        row = matches.iloc[0]
        df.drop('_po_normalized', axis=1, inplace=True)

        return self._row_to_po_record(row, sheet_name, idx)

    def find_by_invoice_number(self, invoice_number: str, sheet_name: str) -> Optional[PORecord]:
        """
        Find a PO record by invoice number in the INVOICE NO. column.

        Handles multiline invoice number cells (e.g. 'INV26790\\nINV27927').
        """
        if not invoice_number or not str(invoice_number).strip():
            return None

        df = self._read_sheet_with_header_detection(sheet_name)
        if df is None:
            return None

        inv_col = None
        for col in df.columns:
            if 'INVOICE NO' in col.upper():
                inv_col = col
                break

        if inv_col is None:
            return None

        inv_clean = str(invoice_number).strip().upper()

        # Check each row — cells may contain multiple invoice numbers separated by newlines
        for idx, row in df.iterrows():
            cell_val = str(row.get(inv_col, '')).strip()
            if not cell_val or cell_val == 'nan':
                continue
            # Split on newlines and check each part
            parts = [p.strip().upper() for p in cell_val.split('\n') if p.strip()]
            if inv_clean in parts:
                return self._row_to_po_record(row, sheet_name, idx)

        return None

    def find_po_candidates(self, sheet_name: str, invoice) -> List[Tuple[PORecord, float]]:
        """
        Find candidate PO records using fuzzy multi-field matching.

        Scores candidates by store name, company/supplier name, and amount proximity.
        Returns list of (PORecord, score) sorted by score descending.
        """
        from ..utils import StringMatcher

        df = self._read_sheet_with_header_detection(sheet_name)
        if df is None:
            return []

        string_matcher = StringMatcher()
        candidates = []

        for idx, row in df.iterrows():
            score = 0.0

            # Store name matching (highest weight)
            po_store = self._safe_str(row.get('STORE'))
            if po_store and invoice.store_location:
                store_score = string_matcher.fuzzy_match_score(
                    invoice.store_location, po_store
                )
                score += store_score * 0.5  # 50% weight

            # Company/supplier name matching (25% weight)
            company = self._safe_str(row.get('COMPANY NAME')) or self._safe_str(row.get('SUPPLIER'))
            if company and invoice.supplier_name:
                company_score = string_matcher.fuzzy_match_score(
                    invoice.supplier_name, company
                )
                score += company_score * 0.25

            # Amount proximity (25% weight)
            quote_val = self._safe_str(row.get('QUOTE OVER £200'))
            inv_amount_col = None
            for col in df.columns:
                if 'INVOICE AMOUNT' in col.upper():
                    inv_amount_col = col
                    break
            po_amount = self._safe_decimal(row.get(inv_amount_col)) if inv_amount_col else None
            po_quote = self._safe_decimal(quote_val) if quote_val else None

            ref_amount = po_amount or po_quote
            if ref_amount and invoice.net_amount and ref_amount > 0:
                ratio = float(min(invoice.net_amount, ref_amount) / max(invoice.net_amount, ref_amount))
                score += ratio * 100 * 0.25

            if score > 0:
                po_record = self._row_to_po_record(row, sheet_name, idx)
                candidates.append((po_record, score))

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates

    def _row_to_po_record(self, row: pd.Series, sheet_name: str, row_index: int) -> PORecord:
        """Convert a DataFrame row to a PORecord."""
        # Extract company name from either COMPANY NAME or SUPPLIER column
        company_name = self._safe_str(row.get('COMPANY NAME')) or self._safe_str(row.get('SUPPLIER'))

        return PORecord(
            po_number=self._safe_str(row.get('PO')),
            sheet_name=sheet_name,
            row_index=row_index,
            store=self._safe_str(row.get('STORE')),
            originator=self._safe_str(row.get('ORIGINATOR')),
            date=self._safe_date(row.get('DATE')),
            job_description=self._safe_str(row.get('JOB DESCRIPTION')) or self._safe_str(row.get('ORDER DETAILS')),
            quote_over_200=self._safe_str(row.get('QUOTE OVER £200')),
            authorized=self._safe_str(row.get('AUTHORISED')),
            date_completed=self._safe_date(row.get('DATE COMPLETED')),
            invoice_no=self._safe_str(row.get('INVOICE NO.')),
            invoice_signed=self._safe_date(row.get('INVOICE SIGNED')),
            invoice_amount=self._safe_decimal(row.get('INVOICE AMOUNT (EX VAT)')),
            nominal_code=self._safe_str(row.get('NOMINAL CODE')),
            brand=self._safe_str(row.get('BRAND')),
            ticket_no=self._safe_str(row.get('TICKET NO.')),
            company_name=company_name,
        )

    @staticmethod
    def _safe_str(value) -> Optional[str]:
        """Convert value to string, handling NaN."""
        if pd.isna(value) or value is None:
            return None
        s = str(value).strip()
        # Clean up PO values that have embedded newlines
        s = s.strip('\n').strip()
        return s if s else None

    @staticmethod
    def _safe_decimal(value) -> Optional[Decimal]:
        """Convert value to Decimal, handling NaN and currency symbols."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            s = str(value).replace(',', '').replace('£', '').strip()
            # Handle multiline amounts (take first one)
            if '\n' in s:
                s = s.split('\n')[0].strip()
            return Decimal(s)
        except Exception:
            return None

    def _safe_date(self, value):
        """Convert value to datetime."""
        if pd.isna(value) or value == '' or value is None:
            return None
        return self.date_parser.parse_date(str(value))

    def load_nominal_code_mapping(self) -> dict:
        """Load supplier -> nominal code mapping from cost centre file tab 3."""
        try:
            df = pd.read_excel(
                self.cost_centre_path,
                sheet_name=2,  # Tab 3 (0-indexed)
            )
            mapping = {}
            for _, row in df.iterrows():
                supplier = str(row.iloc[0]).strip()
                code = str(row.iloc[1]).strip()
                if supplier and code and supplier != 'nan' and code != 'nan':
                    mapping[supplier.lower()] = code
            return mapping
        except Exception:
            return {}

    def get_store_list(self) -> List[str]:
        """Get list of all valid store names from Cost Centre Summary."""
        df = self.load_cost_centre_summary()
        if df.empty:
            return []

        stores = df.iloc[:, 0].dropna().tolist()
        return [str(store).strip() for store in stores if store]
