"""
Quote authorization validator for £200+ invoices.
"""

from decimal import Decimal

from ..models import Invoice, PORecord, Validation, ValidationSeverity


class QuoteValidator:
    """Validator for quote authorization on invoices over £200."""

    def __init__(self, threshold: Decimal = Decimal("200.00")):
        """
        Initialize quote validator.

        Args:
            threshold: Amount threshold requiring quote authorization (default £200)
        """
        self.threshold = threshold

    def validate(self, invoice: Invoice, po_record: PORecord) -> Validation:
        """
        Validate quote authorization for invoices over the threshold.

        Logic:
        - If invoice amount (ex-VAT) > £200:
          - Check "QUOTE OVER £200" column
          - Check "AUTHORISED" column
          - PASS with no warnings if both present
          - WARN (but still match) if either is missing

        Args:
            invoice: Invoice to validate
            po_record: Matching PO record

        Returns:
            Validation result
        """
        # Check if invoice amount exceeds threshold
        if invoice.net_amount <= self.threshold:
            # No authorization required
            return Validation(
                check_name="Quote Authorization (£200+ Check)",
                passed=True,
                expected="No authorization required",
                actual=f"Amount £{invoice.net_amount:.2f} ≤ £{self.threshold:.2f}",
                severity=ValidationSeverity.INFO,
                message=f"Invoice amount £{invoice.net_amount:.2f} is below £{self.threshold:.2f} threshold - no quote authorization required",
            )

        # Amount is over threshold - check authorization
        has_quote_ref = bool(
            po_record.quote_over_200 and str(po_record.quote_over_200).strip()
        )
        has_authorization = bool(
            po_record.authorized and str(po_record.authorized).strip()
        )

        # Case 1: Has quote reference AND authorization → PASS
        if has_quote_ref and has_authorization:
            return Validation(
                check_name="Quote Authorization (£200+ Check)",
                passed=True,
                expected="Quote reference and authorization present",
                actual=f"Quote: {po_record.quote_over_200}, Auth: {po_record.authorized}",
                severity=ValidationSeverity.INFO,
                message=f"Quote authorized: Quote ref '{po_record.quote_over_200}', Authorized by '{po_record.authorized}'",
            )

        sheet = po_record.sheet_name
        row = po_record.row_index + 1

        # Case 2: Has quote reference but NO authorization → WARN
        if has_quote_ref and not has_authorization:
            return Validation(
                check_name="Quote Authorization (£200+ Check)",
                passed=False,
                expected="Quote reference AND authorization",
                actual=f"Quote: {po_record.quote_over_200}, Auth: MISSING",
                severity=ValidationSeverity.WARNING,
                message=f"Over £200 — quote '{po_record.quote_over_200}' present but 'AUTHORISED' is empty (sheet '{sheet}', row {row})",
            )

        # Case 3: No quote reference at all → WARN
        if not has_quote_ref and not has_authorization:
            return Validation(
                check_name="Quote Authorization (£200+ Check)",
                passed=False,
                expected="Quote reference and authorization",
                actual="No quote reference found",
                severity=ValidationSeverity.WARNING,
                message=f"Over £200 — 'QUOTE OVER £200' and 'AUTHORISED' are both empty (sheet '{sheet}', row {row})",
            )

        # Case 4: Has authorization but no quote reference → WARN
        return Validation(
            check_name="Quote Authorization (£200+ Check)",
            passed=False,
            expected="Quote reference and authorization",
            actual=f"No quote ref, Auth: {po_record.authorized}",
            severity=ValidationSeverity.WARNING,
            message=f"Over £200 — authorized by '{po_record.authorized}' but 'QUOTE OVER £200' is empty (sheet '{sheet}', row {row})",
        )
