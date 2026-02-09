"""
PO matcher for finding matching Purchase Order records.

Uses a multi-strategy approach:
  1. PO number substring match (if invoice has a PO)
  2. Invoice number match (search INVOICE NO. column)
  3. Fuzzy multi-field match (store, supplier, amount)
"""
from typing import Optional, List, Tuple
import pandas as pd

from ..models import Invoice, PORecord, Validation, ValidationSeverity
from ..processors import ExcelReader, SheetSelector
from ..utils import StringMatcher


class POMatcher:
    """Matcher for finding PO records corresponding to invoices."""

    FUZZY_MATCH_THRESHOLD = 40.0  # Minimum score for fuzzy match acceptance

    def __init__(self, excel_reader: ExcelReader):
        self.excel_reader = excel_reader
        self.string_matcher = StringMatcher()
        self.maintenance_sheets = {}

    def load_sheets(self):
        """Load all maintenance sheets into memory."""
        self.maintenance_sheets = self.excel_reader.load_maintenance_sheets()

    def find_po_record(self, invoice: Invoice) -> tuple:
        """
        Find the PO record matching an invoice using multi-strategy matching.

        Strategy order:
        1. PO number match (substring/contains) — if invoice has a PO
        2. Invoice number match — search INVOICE NO. column
        3. Fuzzy multi-field match — store + supplier + amount scoring

        Returns:
            Tuple of (PORecord or None, list of Validation results)
        """
        validations = []

        # Determine which sheet to search
        sheet_name = SheetSelector.get_sheet_name(invoice.supplier_type)
        if not sheet_name:
            validations.append(Validation(
                check_name="Sheet Selection",
                passed=False,
                expected="Known supplier type with mapped sheet",
                actual=invoice.supplier_type,
                severity=ValidationSeverity.ERROR,
                message=f"Unknown supplier type '{invoice.supplier_type}', cannot determine sheet"
            ))
            return None, validations

        # Strategy 1: PO number match
        if invoice.po_number and invoice.po_number.strip():
            po_record = self.excel_reader.find_po_record(invoice.po_number, sheet_name)
            if po_record:
                validations.append(Validation(
                    check_name="PO Match",
                    passed=True,
                    expected=f"PO {invoice.po_number} found",
                    actual=f"Found in {sheet_name} sheet (Strategy 1: PO match)",
                    severity=ValidationSeverity.INFO,
                    message=f"PO '{invoice.po_number}' found in sheet '{sheet_name}'"
                ))
                self._add_post_match_validations(invoice, po_record, validations)
                return po_record, validations

        # Strategy 2: Invoice number match
        if invoice.invoice_number and invoice.invoice_number.strip():
            po_record = self.excel_reader.find_by_invoice_number(
                invoice.invoice_number, sheet_name
            )
            if po_record:
                validations.append(Validation(
                    check_name="PO Match",
                    passed=True,
                    expected=f"Invoice {invoice.invoice_number} found",
                    actual=f"Found in {sheet_name} sheet (Strategy 2: invoice # match)",
                    severity=ValidationSeverity.INFO,
                    message=f"Invoice '{invoice.invoice_number}' already recorded in sheet '{sheet_name}' for PO '{po_record.po_number}'"
                ))
                self._add_post_match_validations(invoice, po_record, validations)
                return po_record, validations

        # Strategy 3: Fuzzy multi-field match
        candidates = self.excel_reader.find_po_candidates(sheet_name, invoice)

        if candidates:
            best_record, best_score = candidates[0]

            if best_score >= self.FUZZY_MATCH_THRESHOLD:
                match_details = f"score={best_score:.1f}"
                if not invoice.po_number:
                    match_details += ", no PO on invoice"

                validations.append(Validation(
                    check_name="PO Match",
                    passed=True,
                    expected="Matching PO record",
                    actual=f"Found PO '{best_record.po_number}' in {sheet_name} (Strategy 3: fuzzy match, {match_details})",
                    severity=ValidationSeverity.WARNING if best_score < 60 else ValidationSeverity.INFO,
                    message=f"Fuzzy matched to PO '{best_record.po_number}' in '{sheet_name}' (store='{best_record.store}', score={best_score:.1f})"
                ))

                if not invoice.po_number:
                    validations.append(Validation(
                        check_name="PO Number Warning",
                        passed=True,
                        expected="PO number on invoice",
                        actual="No PO found on invoice",
                        severity=ValidationSeverity.WARNING,
                        message="No PO number found on invoice — matched using store/supplier/amount"
                    ))

                self._add_post_match_validations(invoice, best_record, validations)
                return best_record, validations

            # Score too low — report closest candidates
            candidate_info = "; ".join(
                f"PO '{c[0].po_number}' store='{c[0].store}' (score={c[1]:.1f})"
                for c in candidates[:3]
            )
            validations.append(Validation(
                check_name="PO Match",
                passed=False,
                expected="Matching PO record with score >= {:.0f}".format(self.FUZZY_MATCH_THRESHOLD),
                actual=f"Best score {best_score:.1f}. Closest: {candidate_info}",
                severity=ValidationSeverity.ERROR,
                message=f"No confident match found in '{sheet_name}'. Closest candidates: {candidate_info}"
            ))
            return None, validations

        # No match at all
        details = f"PO='{invoice.po_number}'" if invoice.po_number else "no PO on invoice"
        validations.append(Validation(
            check_name="PO Match",
            passed=False,
            expected=f"Match in {sheet_name} sheet",
            actual=f"No match found ({details})",
            severity=ValidationSeverity.ERROR,
            message=f"No matching PO record found in sheet '{sheet_name}' ({details})"
        ))
        return None, validations

    def _add_post_match_validations(self, invoice: Invoice, po_record: PORecord, validations: list):
        """Add duplicate check and store match validations after a PO match is found."""
        # Check if PO already has an invoice number
        if po_record.is_invoiced():
            validations.append(Validation(
                check_name="Duplicate Invoice Check",
                passed=False,
                expected="PO not yet invoiced",
                actual=f"Already invoiced: {po_record.invoice_no}",
                severity=ValidationSeverity.ERROR,
                message=f"PO '{po_record.po_number}' already has invoice number '{po_record.invoice_no}'"
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

            if match_score >= 70:
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
