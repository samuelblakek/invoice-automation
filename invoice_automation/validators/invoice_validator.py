"""
Invoice validator orchestrator - coordinates all validation checks.
"""

from decimal import Decimal
from typing import List, Optional

from ..models import (
    Invoice,
    PORecord,
    ValidationResult,
    Validation,
    ValidationSeverity,
)
from ..processors import ExcelReader
from .po_matcher import POMatcher
from .quote_validator import QuoteValidator


class InvoiceValidator:
    """Main validator that orchestrates all validation checks."""

    def __init__(
        self, excel_reader: ExcelReader, quote_threshold: Decimal = Decimal("200.00")
    ):
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
            invoice=invoice, po_record=None, pdf_path=invoice.pdf_path
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

        # Step 4: Validate amounts (positivity, reconciliation, PO cross-check)
        for amount_validation in self._validate_amounts(invoice, po_record):
            result.add_validation(amount_validation)

        # Finalize result
        result.finalize()

        return result

    # An extracted amount may differ from the PO's expected figure by at most
    # this fraction (or AMOUNT_TOLERANCE_ABS, whichever is larger) before it is
    # flagged for review.
    AMOUNT_TOLERANCE_PCT = Decimal("0.01")
    AMOUNT_TOLERANCE_ABS = Decimal("0.50")

    def _validate_amounts(
        self, invoice: Invoice, po_record: Optional[PORecord]
    ) -> List[Validation]:
        """Validate amounts: positivity, net+VAT==total, and PO cross-check.

        Returns a list of Validation results. A reconciliation/cross-check
        mismatch is raised as an ERROR with check_name 'Amount Reconciliation',
        which blocks auto-update but is treated as reviewable (the user can
        confirm) — see ValidationResult.needs_review.
        """
        validations: List[Validation] = []

        if invoice.net_amount <= 0:
            validations.append(
                Validation(
                    check_name="Amount Validation",
                    passed=False,
                    expected="Positive amount",
                    actual=f"£{invoice.net_amount}",
                    severity=ValidationSeverity.ERROR,
                    message=f"Extracted net amount is £{invoice.net_amount} which is invalid. Check the PDF — the amount may not have been read correctly.",
                )
            )
            return validations

        if invoice.net_amount > Decimal("10000"):
            validations.append(
                Validation(
                    check_name="Amount Validation",
                    passed=True,
                    expected="Amount under £10,000",
                    actual=f"£{invoice.net_amount}",
                    severity=ValidationSeverity.WARNING,
                    message=f"High amount: £{invoice.net_amount} (exceeds £10,000 - please verify)",
                )
            )
        else:
            validations.append(
                Validation(
                    check_name="Amount Validation",
                    passed=True,
                    expected="Valid amount",
                    actual=f"£{invoice.net_amount}",
                    severity=ValidationSeverity.INFO,
                    message=f"Amount validated: £{invoice.net_amount}",
                )
            )

        # Internal consistency: net + VAT should equal total. Only checked when
        # all three were independently extracted (>0); a 0 VAT/total means the
        # field wasn't read, so there is nothing reliable to reconcile against.
        net, vat, total = invoice.net_amount, invoice.vat_amount, invoice.total_amount
        if net > 0 and vat > 0 and total > 0:
            diff = abs((net + vat) - total)
            if diff > max(self.AMOUNT_TOLERANCE_ABS, total * self.AMOUNT_TOLERANCE_PCT):
                validations.append(
                    Validation(
                        check_name="Amount Reconciliation",
                        passed=False,
                        expected=f"net + VAT = total (£{net} + £{vat} = £{net + vat})",
                        actual=f"total £{total} (off by £{diff})",
                        severity=ValidationSeverity.ERROR,
                        message=f"Amounts don't reconcile: net £{net} + VAT £{vat} = £{net + vat}, but total reads £{total}. Likely a mis-read amount — please verify before posting.",
                    )
                )

        # Cross-check the extracted net against the PO's expected ex-VAT amount,
        # when the spreadsheet already records one for this PO.
        if po_record is not None and po_record.invoice_amount and po_record.invoice_amount > 0:
            expected = po_record.invoice_amount
            diff = abs(net - expected)
            if diff > max(self.AMOUNT_TOLERANCE_ABS, expected * self.AMOUNT_TOLERANCE_PCT):
                validations.append(
                    Validation(
                        check_name="Amount Reconciliation",
                        passed=False,
                        expected=f"net ≈ PO amount £{expected}",
                        actual=f"net £{net} (off by £{diff})",
                        severity=ValidationSeverity.ERROR,
                        message=f"Extracted net £{net} differs from the PO's recorded amount £{expected} (sheet '{po_record.sheet_name}', row {po_record.row_index + 1}). Please verify before posting.",
                    )
                )

        return validations
