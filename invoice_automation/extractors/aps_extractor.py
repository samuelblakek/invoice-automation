"""
APS Fire Systems invoice extractor.
"""

from pathlib import Path
import re

from .base_extractor import BaseExtractor
from ..models import Invoice


class APSExtractor(BaseExtractor):
    """Extractor for APS Fire Systems invoices."""

    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data from APS PDF.

        Args:
            pdf_path: Path to the APS invoice PDF

        Returns:
            Invoice object with extracted data
        """
        text = self._extract_text(pdf_path)

        # Try multiple patterns for invoice number
        invoice_number = (
            self._find_pattern(
                text, r"Invoice\s+(?:No\.?|#)?\s*:?\s*(\d+)", re.IGNORECASE
            )
            or self._find_pattern(text, r"NO\.\s*(\d+)", re.IGNORECASE)
            or ""
        )

        # PO number - APS sometimes uses REF instead of PO
        po_number = (
            self._find_pattern(
                text,
                r"(?:Order|PO|P\.O\.)\s*(?:No\.?|#)?\s*:?\s*([A-Z0-9/]+)",
                re.IGNORECASE,
            )
            or self._find_pattern(
                text, r"P/O\s+(?:No\.?|#)?\s*:?\s*([A-Z0-9/]+)", re.IGNORECASE
            )
            or ""
        )

        if not invoice_number:
            # Don't fail - create a generic invoice object
            invoice_number = f"APS_{pdf_path.stem}"

        invoice_date = self.date_parser.parse_date(
            self._find_pattern(
                text,
                r"Invoice Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                re.IGNORECASE,
            )
            or ""
        )

        # Extract store from install address or REF field
        store_location = ""
        store_text = ""
        store_match = re.search(
            r"(?:INSTALL ADDRESS|REF:)(.*?)(?:\n\n|$)", text, re.IGNORECASE | re.DOTALL
        )
        if store_match:
            store_text = store_match.group(1).strip()
            lines = [line.strip() for line in store_text.split("\n") if line.strip()]
            store_location = lines[0] if lines else ""

        # Extract amounts - APS uses "NET TOTAL £ 573.00" format
        net_amount = None

        # Try "NET TOTAL" pattern first (APS specific)
        net_match = re.search(r"NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
        if net_match:
            net_amount = self.amount_parser.parse_amount(net_match.group(1))

        # Fallback to other patterns
        if not net_amount:
            net_amount = self.amount_parser.parse_amount(
                self._find_pattern(
                    text, r"(?:Sub Total|Net)\s*:?\s*£?\s*([\d,]+\.?\d*)", re.IGNORECASE
                )
                or "0"
            )

        # Extract VAT
        vat_amount = self.amount_parser.parse_amount(
            self._find_pattern(
                text, r"VAT\s+@\s+\d+%\s+£\s*([\d,]+\.?\d*)", re.IGNORECASE
            )
            or self._find_pattern(
                text, r"VAT\s*:?\s*£?\s*([\d,]+\.?\d*)", re.IGNORECASE
            )
            or "0"
        )

        # Extract total (with VAT)
        total_amount = self.amount_parser.parse_amount(
            self._find_pattern(text, r"TOTAL\s+DUE\s+£\s*([\d,]+\.?\d*)", re.IGNORECASE)
            or self._find_pattern(
                text, r"Total\s*:?\s*£?\s*([\d,]+\.?\d*)", re.IGNORECASE
            )
            or "0"
        )

        nominal_code = ""

        description = (
            self._find_pattern(
                text,
                r"Description\s*:?\s*(.*?)(?:\n\n|Total)",
                re.IGNORECASE | re.DOTALL,
            )
            or ""
        )
        description = " ".join(description.split())[:500]

        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name="APS Fire Systems",
            supplier_type="APS",
            po_number=po_number,
            store_location=store_location,
            store_address=store_text,
            net_amount=net_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            nominal_code=nominal_code,
            description=description,
            raw_text=text,
            pdf_path=str(pdf_path),
        )

        return invoice
