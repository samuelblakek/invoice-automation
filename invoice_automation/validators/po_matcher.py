"""
PO matcher for finding matching Purchase Order records.

Uses a multi-strategy approach:
  1. PO number substring match (if invoice has a PO)
  2. Invoice number match (search INVOICE NO. column)
  3. Fuzzy multi-field match (store, supplier, amount)
"""

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
            validations.append(
                Validation(
                    check_name="Sheet Selection",
                    passed=False,
                    expected="Known supplier type with mapped sheet",
                    actual=invoice.supplier_type,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unknown supplier type '{invoice.supplier_type}' — can't determine which Excel sheet to search. Process this invoice manually.",
                )
            )
            return None, validations

        # Strategy 1: PO number match (mapped sheet first, then other maintenance sheets)
        if invoice.has_po:
            po_record = self.excel_reader.find_po_record_any_sheet(
                invoice.po_number, sheet_name
            )
            if po_record:
                validations.append(
                    Validation(
                        check_name="PO Match",
                        passed=True,
                        expected=f"PO {invoice.po_number} found",
                        actual=f"Found in {po_record.sheet_name} sheet (Strategy 1: PO match)",
                        severity=ValidationSeverity.INFO,
                        message=f"PO '{invoice.po_number}' found in sheet '{po_record.sheet_name}'",
                    )
                )
                self._add_post_match_validations(invoice, po_record, validations)
                return po_record, validations

        # Strategy 2: Invoice number match
        if invoice.invoice_number and invoice.invoice_number.strip():
            po_record = self.excel_reader.find_by_invoice_number(
                invoice.invoice_number, sheet_name
            )
            if po_record:
                validations.append(
                    Validation(
                        check_name="PO Match",
                        passed=True,
                        expected=f"Invoice {invoice.invoice_number} found",
                        actual=f"Found in {sheet_name} sheet (Strategy 2: invoice # match)",
                        severity=ValidationSeverity.INFO,
                        message=f"Invoice '{invoice.invoice_number}' already recorded in sheet '{sheet_name}' for PO '{po_record.po_number}'",
                    )
                )
                self._add_post_match_validations(invoice, po_record, validations)
                return po_record, validations

        candidates = self.excel_reader.find_po_candidates(sheet_name, invoice)

        # If the invoice states a PO but neither the exact-PO search (Strategy 1)
        # nor the invoice-number search (Strategy 2) found it, report it as NOT
        # FOUND. We deliberately do not fuzzy-match to a *different* PO here —
        # guessing a different order risks invoicing against the wrong PO. Closest
        # candidates are shown only as a hint for manual lookup.
        if invoice.has_po:
            validations.append(
                Validation(
                    check_name="PO Match",
                    passed=False,
                    expected=f"PO '{invoice.po_number}' present in a maintenance sheet",
                    actual="PO stated on the invoice was not found in any sheet",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"PO {invoice.po_number} not found in any maintenance sheet. "
                        f"Check the PO exists and is on the right sheet."
                    ),
                )
            )
            return None, validations

        # Strategy 3: Fuzzy multi-field match — only for invoices with NO PO of
        # their own (scored on store + supplier + amount).
        if not candidates:
            validations.append(
                Validation(
                    check_name="PO Match",
                    passed=False,
                    expected=f"Match in {sheet_name} sheet",
                    actual="No match found (no PO on invoice)",
                    severity=ValidationSeverity.ERROR,
                    message=f"No matching PO found in sheet '{sheet_name}' (no PO on invoice). Check the PO exists in the spreadsheet.",
                )
            )
            return None, validations

        best_record, best_score = candidates[0]

        if best_score >= self.FUZZY_MATCH_THRESHOLD:
            match_fields = []
            if invoice.has_store:
                match_fields.append(f"store '{invoice.store_location}'")
            if invoice.supplier_name and invoice.supplier_name.strip():
                match_fields.append(f"supplier '{invoice.supplier_name}'")
            if invoice.net_amount > 0:
                match_fields.append(f"amount £{invoice.net_amount:.2f}")
            fields_str = ", ".join(match_fields) if match_fields else "available fields"
            # No PO number on the invoice: this is a best-GUESS match, never an
            # auto-update. Real matching is on the PO number; without one we surface
            # a candidate for a human to confirm. Severity ERROR blocks
            # can_auto_update; check_name "PO Match" keeps it in the reviewable set
            # (see ValidationResult.needs_review), so it lands in Needs Review.
            validations.append(
                Validation(
                    check_name="PO Match",
                    passed=False,
                    expected="A PO number printed on the invoice",
                    actual=f"No PO on invoice; closest guess is PO '{best_record.po_number}' (score={best_score:.1f})",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"NEEDS REVIEW — no PO number on this invoice. Best guess is "
                        f"PO '{best_record.po_number}' ({best_record.store}), matched only by "
                        f"{fields_str}. This is NOT a confirmed PO match: check it is the "
                        f"correct order before approving."
                    ),
                )
            )

            self._add_post_match_validations(invoice, best_record, validations)
            return best_record, validations

        # Below the fuzzy threshold — no confident match.
        validations.append(
            Validation(
                check_name="PO Match",
                passed=False,
                expected="Matching PO record with score >= {:.0f}".format(
                    self.FUZZY_MATCH_THRESHOLD
                ),
                actual=f"Best score {best_score:.1f}, below threshold",
                severity=ValidationSeverity.ERROR,
                message=f"No matching PO found in sheet '{sheet_name}' — there is no PO number on the invoice. Check the PO exists and the supplier and store are correct.",
            )
        )

        # Score 25-39: return best candidate as a reviewable near-miss; below 25,
        # there is nothing worth surfacing.
        if best_score >= 25:
            self._add_post_match_validations(invoice, best_record, validations)
            return best_record, validations
        return None, validations

    def _add_post_match_validations(
        self, invoice: Invoice, po_record: PORecord, validations: list
    ):
        """Add duplicate check and store match validations after a PO match is found."""
        # Check if PO already has an invoice number
        if po_record.is_invoiced():
            validations.append(
                Validation(
                    check_name="Duplicate Invoice Check",
                    passed=False,
                    expected="PO not yet invoiced",
                    actual=f"Already invoiced: {po_record.invoice_no}",
                    severity=ValidationSeverity.ERROR,
                    message=f"PO '{po_record.po_number}' already invoiced as '{po_record.invoice_no}' (sheet '{po_record.sheet_name}', row {po_record.row_index + 1}). If this is a different invoice for the same PO, update manually.",
                )
            )
        else:
            validations.append(
                Validation(
                    check_name="Duplicate Invoice Check",
                    passed=True,
                    expected="PO not yet invoiced",
                    actual="No existing invoice",
                    severity=ValidationSeverity.INFO,
                    message="PO is available for invoicing",
                )
            )

        # Validate store name matches (fuzzy match)
        if invoice.has_store and po_record.store:
            match_score = self.string_matcher.fuzzy_match_score(
                invoice.store_location, po_record.store
            )

            if match_score >= 70:
                validations.append(
                    Validation(
                        check_name="Store Match",
                        passed=True,
                        expected=po_record.store,
                        actual=f"{invoice.store_location} ({match_score}% match)",
                        severity=ValidationSeverity.INFO,
                        message=f"Store name matches: '{invoice.store_location}' ≈ '{po_record.store}' ({match_score}%)",
                    )
                )
            else:
                severity = (
                    ValidationSeverity.WARNING
                    if match_score >= 50
                    else ValidationSeverity.ERROR
                )
                validations.append(
                    Validation(
                        check_name="Store Match",
                        passed=(severity == ValidationSeverity.WARNING),
                        expected=po_record.store,
                        actual=f"{invoice.store_location} ({match_score}% match)",
                        severity=severity,
                        message=f"Store mismatch: invoice says '{invoice.store_location}' but PO says '{po_record.store}' ({match_score}% match, sheet '{po_record.sheet_name}', row {po_record.row_index + 1}).",
                    )
                )
