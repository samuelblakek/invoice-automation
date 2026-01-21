"""
Excel reader for loading reference data and PO records.
"""
from pathlib import Path
from typing import Dict, List
import pandas as pd
from decimal import Decimal

from ..models import PORecord
from ..utils import DateParser


class ExcelReader:
    """Reader for loading data from Excel workbooks."""

    def __init__(self, maintenance_workbook_path: Path, cost_centre_path: Path):
        """
        Initialize Excel reader with file paths.

        Args:
            maintenance_workbook_path: Path to Maintenance PO workbook
            cost_centre_path: Path to Cost Centre Summary workbook
        """
        self.maintenance_workbook_path = Path(maintenance_workbook_path)
        self.cost_centre_path = Path(cost_centre_path)
        self.date_parser = DateParser()

    def load_maintenance_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        Load all maintenance PO sheets from the workbook.

        Returns:
            Dictionary mapping sheet name to DataFrame
        """
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
            try:
                df = pd.read_excel(
                    self.maintenance_workbook_path,
                    sheet_name=sheet_name,
                    dtype=str  # Read as strings to preserve formatting
                )
                sheets[sheet_name] = df
            except Exception as e:
                print(f"Warning: Could not load sheet '{sheet_name}': {e}")

        return sheets

    def load_codes_sheet(self) -> pd.DataFrame:
        """
        Load the CODES reference sheet.

        Returns:
            DataFrame with nominal code mappings
        """
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
        """
        Load the Cost Centre Summary (store addresses).

        Returns:
            DataFrame with store locations and addresses
        """
        try:
            df = pd.read_excel(
                self.cost_centre_path,
                sheet_name='Cost Centre Summary SK'
            )
            return df
        except Exception as e:
            print(f"Warning: Could not load Cost Centre Summary: {e}")
            return pd.DataFrame()

    def find_po_record(self, po_number: str, sheet_name: str) -> PORecord:
        """
        Find a PO record in a specific sheet.

        Args:
            po_number: PO number to find
            sheet_name: Sheet name to search in

        Returns:
            PORecord if found, None otherwise
        """
        # Load the specific sheet
        try:
            df = pd.read_excel(
                self.maintenance_workbook_path,
                sheet_name=sheet_name,
                dtype=str
            )
        except Exception as e:
            print(f"Error loading sheet '{sheet_name}': {e}")
            return None

        # Find matching PO using vectorized operations (much faster than iterrows)
        po_clean = str(po_number).strip().upper()

        # Create normalized PO column for matching
        if 'PO' not in df.columns:
            return None

        df['_po_normalized'] = df['PO'].fillna('').astype(str).str.strip().str.upper()

        # Find matching rows
        matches = df[df['_po_normalized'] == po_clean]

        if matches.empty:
            return None

        # Get first match
        idx = matches.index[0]
        row = matches.iloc[0]

        # Clean up temporary column
        df.drop('_po_normalized', axis=1, inplace=True)

        return self._row_to_po_record(row, sheet_name, idx)

    def _row_to_po_record(self, row: pd.Series, sheet_name: str, row_index: int) -> PORecord:
        """
        Convert a DataFrame row to a PORecord.

        Args:
            row: DataFrame row
            sheet_name: Sheet name
            row_index: Row index in the sheet

        Returns:
            PORecord object
        """
        def safe_decimal(value):
            """Convert value to Decimal, handling NaN and empty strings."""
            if pd.isna(value) or value == '' or value is None:
                return None
            try:
                return Decimal(str(value).replace(',', ''))
            except:
                return None

        def safe_date(value):
            """Convert value to datetime."""
            if pd.isna(value) or value == '' or value is None:
                return None
            return self.date_parser.parse_date(str(value))

        def safe_str(value):
            """Convert value to string, handling NaN."""
            if pd.isna(value) or value is None:
                return None
            return str(value).strip()

        return PORecord(
            po_number=safe_str(row.get('PO')),
            sheet_name=sheet_name,
            row_index=row_index,
            store=safe_str(row.get('STORE')),
            originator=safe_str(row.get('ORIGINATOR')),
            date=safe_date(row.get('DATE')),
            job_description=safe_str(row.get('JOB DESCRIPTION')),
            quote_over_200=safe_str(row.get('QUOTE OVER £200')),
            authorized=safe_str(row.get('AUTHORISED')),
            date_completed=safe_date(row.get('DATE COMPLETED')),
            invoice_no=safe_str(row.get('INVOICE NO.')),
            invoice_signed=safe_date(row.get('INVOICE SIGNED')),
            invoice_amount=safe_decimal(row.get('INVOICE AMOUNT (EX VAT)')),
            nominal_code=safe_str(row.get('NOMINAL CODE')),
            brand=safe_str(row.get('BRAND')),
            ticket_no=safe_str(row.get('TICKET NO.'))
        )

    def get_store_list(self) -> List[str]:
        """
        Get list of all valid store names from Cost Centre Summary.

        Returns:
            List of store names
        """
        df = self.load_cost_centre_summary()
        if df.empty:
            return []

        # Extract store names from first column
        stores = df.iloc[:, 0].dropna().tolist()
        return [str(store).strip() for store in stores if store]
