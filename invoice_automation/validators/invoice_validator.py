"""
Invoice validator orchestrator - coordinates all validation checks.
"""
from pathlib import Path
from decimal import Decimal

from ..models import Invoice, ValidationResult, Validation, ValidationSeverity
from ..processors import ExcelReader
from .po_matcher import POMatcher
from .quote_validator import QuoteValidator


class InvoiceValidator:
    """Main validator that orchestrates all validation checks."""

    def __init__(self, excel_reader: ExcelReader, quote_threshold: Decimal = Decimal('200.00')):
        """
        Initialize invoice validator.

        Args:
            excel_reader: ExcelReader for loading reference data
            quote_threshold: Amount threshold for quote authorization (default £200)
        """
        self.excel_reader = excel_reader
        self.po_matcher = POMatcher(excel_reader)
        self.quote_validator = QuoteValidator(threshold=quote_threshold)

        # Load reference data
        self.po_matcher.load_sheets()
        self.cost_centre_df = excel_reader.load_cost_centre_summary()
        self.codes_df = excel_reader.load_codes_sheet()

    def validate(self, invoice: Invoice) -> ValidationResult:
        """
        Perform all validations on an invoice.

        Validation sequence:
        1. Find matching PO record
        2. Check if PO already invoiced
        3. Validate store match
        4. Validate nominal code
        5. Check quote authorization for £200+
        6. Validate amounts

        Args:
            invoice: Invoice to validate

        Returns:
            ValidationResult with all checks performed
        """
        result = ValidationResult(
            invoice=invoice,
            po_record=None,
            pdf_path=invoice.pdf_path
        )

        # Step 1: Find PO record
        po_record, po_validations = self.po_matcher.find_po_record(invoice)
        result.po_record = po_record

        # Add PO matching validations
        for validation in po_validations:
            result.add_validation(validation)

        # If PO not found or already invoiced, stop here
        if po_record is None:
            result.finalize()
            return result

        if po_record.is_invoiced():
            result.finalize()
            return result

        # Step 2: Validate nominal code
        nominal_validation = self._validate_nominal_code(invoice, po_record)
        result.add_validation(nominal_validation)

        # Step 3: Validate quote authorization (£200+ check)
        quote_validation = self.quote_validator.validate(invoice, po_record)
        result.add_validation(quote_validation)

        # Step 4: Validate amounts
        amount_validation = self._validate_amounts(invoice)
        result.add_validation(amount_validation)

        # Step 5: Validate VAT calculation
        vat_validation = self._validate_vat(invoice)
        result.add_validation(vat_validation)

        # Finalize result
        result.finalize()

        return result

    def _validate_nominal_code(self, invoice: Invoice, po_record) -> Validation:
        """Validate nominal code matches expectations."""
        invoice_code = invoice.nominal_code
        po_code = po_record.nominal_code

        # If neither has a code, it's a warning
        if not invoice_code and not po_code:
            return Validation(
                check_name="Nominal Code",
                passed=True,  # Don't block, but flag
                expected="Nominal code present",
                actual="Missing from both invoice and PO",
                severity=ValidationSeverity.WARNING,
                message="Nominal code missing from both invoice and PO record"
            )

        # If both have codes and they match
        if invoice_code and po_code and invoice_code == po_code:
            return Validation(
                check_name="Nominal Code",
                passed=True,
                expected=po_code,
                actual=invoice_code,
                severity=ValidationSeverity.INFO,
                message=f"Nominal code matches: {invoice_code}"
            )

        # If they don't match
        if invoice_code and po_code and invoice_code != po_code:
            return Validation(
                check_name="Nominal Code",
                passed=False,
                expected=po_code,
                actual=invoice_code,
                severity=ValidationSeverity.WARNING,  # Warning, not error
                message=f"Nominal code mismatch: invoice={invoice_code}, PO={po_code}"
            )

        # If only one has a code, it's acceptable
        code = invoice_code or po_code
        return Validation(
            check_name="Nominal Code",
            passed=True,
            expected="Nominal code present",
            actual=code,
            severity=ValidationSeverity.INFO,
            message=f"Nominal code: {code} (from {'invoice' if invoice_code else 'PO'})"
        )

    def _validate_amounts(self, invoice: Invoice) -> Validation:
        """Validate amounts are positive and reasonable."""
        if invoice.net_amount <= 0:
            return Validation(
                check_name="Amount Validation",
                passed=False,
                expected="Positive amount",
                actual=f"£{invoice.net_amount}",
                severity=ValidationSeverity.ERROR,
                message=f"Extracted net amount is £{invoice.net_amount} which is invalid. Check the PDF — the amount may not have been read correctly."
            )

        if invoice.net_amount > Decimal('10000'):
            return Validation(
                check_name="Amount Validation",
                passed=True,
                expected="Amount under £10,000",
                actual=f"£{invoice.net_amount}",
                severity=ValidationSeverity.WARNING,
                message=f"High amount: £{invoice.net_amount} (exceeds £10,000 - please verify)"
            )

        return Validation(
            check_name="Amount Validation",
            passed=True,
            expected="Valid amount",
            actual=f"£{invoice.net_amount}",
            severity=ValidationSeverity.INFO,
            message=f"Amount validated: £{invoice.net_amount}"
        )

    def _validate_vat(self, invoice: Invoice) -> Validation:
        """Validate VAT calculation."""
        if not invoice.net_amount or not invoice.vat_amount or not invoice.total_amount:
            return Validation(
                check_name="VAT Calculation",
                passed=True,
                expected="VAT calculation verified",
                actual="Insufficient data",
                severity=ValidationSeverity.INFO,
                message="VAT calculation not verified (missing data)"
            )

        calculated_total = invoice.net_amount + invoice.vat_amount
        tolerance = Decimal('0.02')  # 2p tolerance for rounding

        if abs(calculated_total - invoice.total_amount) <= tolerance:
            return Validation(
                check_name="VAT Calculation",
                passed=True,
                expected=f"£{calculated_total:.2f}",
                actual=f"£{invoice.total_amount:.2f}",
                severity=ValidationSeverity.INFO,
                message=f"VAT calculation correct: £{invoice.net_amount:.2f} + £{invoice.vat_amount:.2f} = £{invoice.total_amount:.2f}"
            )

        return Validation(
            check_name="VAT Calculation",
            passed=False,
            expected=f"£{calculated_total:.2f}",
            actual=f"£{invoice.total_amount:.2f}",
            severity=ValidationSeverity.WARNING,
            message=f"VAT calculation mismatch: Net £{invoice.net_amount:.2f} + VAT £{invoice.vat_amount:.2f} ≠ Total £{invoice.total_amount:.2f}"
        )
