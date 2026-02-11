"""
Invoice validator orchestrator - coordinates all validation checks.
"""
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

        # Step 2: Validate quote authorization (£200+ check)
        quote_validation = self.quote_validator.validate(invoice, po_record)
        result.add_validation(quote_validation)

        # Step 4: Validate amounts
        amount_validation = self._validate_amounts(invoice)
        result.add_validation(amount_validation)

        # Finalize result
        result.finalize()

        return result

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

