"""
PO matcher for finding matching Purchase Order records.
"""
from typing import Optional, Dict
import pandas as pd

from ..models import Invoice, PORecord, Validation, ValidationSeverity
from ..processors import ExcelReader, SheetSelector
from ..utils import StringMatcher


class POMatcher:
    """Matcher for finding PO records corresponding to invoices."""

    def __init__(self, excel_reader: ExcelReader):
        """
        Initialize PO matcher.

        Args:
            excel_reader: ExcelReader instance for loading PO data
        """
        self.excel_reader = excel_reader
        self.string_matcher = StringMatcher()
        self.maintenance_sheets = {}

    def load_sheets(self):
        """Load all maintenance sheets into memory."""
        self.maintenance_sheets = self.excel_reader.load_maintenance_sheets()

    def find_po_record(self, invoice: Invoice) -> tuple:
        """
        Find the PO record matching an invoice.

        Args:
            invoice: Invoice to match

        Returns:
            Tuple of (PORecord or None, list of Validation results)
        """
        validations = []

        # Determine which sheet to search based on supplier
        sheet_name = SheetSelector.get_sheet_name(invoice.supplier_type)
        if not sheet_name:
            validations.append(Validation(
                check_name="Sheet Selection",
                passed=False,
                expected=f"Known supplier type with mapped sheet",
                actual=invoice.supplier_type,
                severity=ValidationSeverity.ERROR,
                message=f"Unknown supplier type '{invoice.supplier_type}', cannot determine sheet"
            ))
            return None, validations

        # Search for PO in the sheet
        po_record = self.excel_reader.find_po_record(invoice.po_number, sheet_name)

        if po_record is None:
            # PO not found
            validations.append(Validation(
                check_name="PO Match",
                passed=False,
                expected=f"PO {invoice.po_number} found in {sheet_name} sheet",
                actual="PO not found",
                severity=ValidationSeverity.ERROR,
                message=f"PO number '{invoice.po_number}' not found in sheet '{sheet_name}'"
            ))
            return None, validations

        # PO found - validate it
        validations.append(Validation(
            check_name="PO Match",
            passed=True,
            expected=f"PO {invoice.po_number} found",
            actual=f"Found in {sheet_name} sheet",
            severity=ValidationSeverity.INFO,
            message=f"PO '{invoice.po_number}' found in sheet '{sheet_name}'"
        ))

        # Check if PO already has an invoice number
        if po_record.is_invoiced():
            validations.append(Validation(
                check_name="Duplicate Invoice Check",
                passed=False,
                expected="PO not yet invoiced",
                actual=f"Already invoiced: {po_record.invoice_no}",
                severity=ValidationSeverity.ERROR,
                message=f"PO '{invoice.po_number}' already has invoice number '{po_record.invoice_no}'"
            ))
        else:
            validations.append(Validation(
                check_name="Duplicate Invoice Check",
                passed=True,
                expected="PO not yet invoiced",
                actual="No existing invoice",
                severity=ValidationSeverity.INFO,
                message="PO is available for invoicing"
            ))

        # Validate store name matches (fuzzy match)
        if invoice.store_location and po_record.store:
            match_score = self.string_matcher.fuzzy_match_score(
                invoice.store_location,
                po_record.store
            )

            if match_score >= 70:  # Threshold for acceptance
                validations.append(Validation(
                    check_name="Store Match",
                    passed=True,
                    expected=po_record.store,
                    actual=f"{invoice.store_location} ({match_score}% match)",
                    severity=ValidationSeverity.INFO,
                    message=f"Store name matches: '{invoice.store_location}' ≈ '{po_record.store}' ({match_score}%)"
                ))
            else:
                severity = ValidationSeverity.WARNING if match_score >= 50 else ValidationSeverity.ERROR
                validations.append(Validation(
                    check_name="Store Match",
                    passed=(severity == ValidationSeverity.WARNING),
                    expected=po_record.store,
                    actual=f"{invoice.store_location} ({match_score}% match)",
                    severity=severity,
                    message=f"Store name mismatch: invoice='{invoice.store_location}', PO='{po_record.store}' ({match_score}%)"
                ))

        return po_record, validations
