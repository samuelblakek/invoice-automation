"""
CJL Group invoice extractor.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
import re

from .base_extractor import BaseExtractor, PDFExtractionError
from ..models import Invoice


class CJLExtractor(BaseExtractor):
    """Extractor for CJL Group invoices."""

    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data from CJL Group PDF.

        Expected format:
        - Invoice #: 28564
        - P.O.#: 110075/CJL316
        - Invoice Date: 12 May 2025
        - Subject: Unit 3, Cascades Shopping Centre, Portsmouth
        - Sub Total: 518.00
        - Standard Rate (20%): 103.60
        - Total: £621.60

        Args:
            pdf_path: Path to the CJL invoice PDF

        Returns:
            Invoice object with extracted data

        Raises:
            PDFExtractionError: If extraction fails
        """
        # Extract text from PDF
        text = self._extract_text(pdf_path)

        # Extract invoice number
        invoice_number = self._extract_invoice_number(text)
        if not invoice_number:
            raise PDFExtractionError(
                "Could not extract invoice number from CJL invoice"
            )

        # Extract PO number
        po_number = self._extract_po_number(text)
        if not po_number:
            raise PDFExtractionError("Could not extract PO number from CJL invoice")

        # Extract date
        invoice_date = self._extract_invoice_date(text)

        # Extract store information
        store_location, store_address = self._extract_store_info(text)

        # Extract amounts
        net_amount, vat_amount, total_amount = self._extract_amounts(text)
        if not net_amount:
            raise PDFExtractionError("Could not extract amounts from CJL invoice")

        # Extract description
        description = self._extract_description(text)

        nominal_code = ""

        # Create invoice object
        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name="CJL Group Ltd",
            supplier_type="CJL",
            po_number=po_number,
            store_location=store_location,
            store_address=store_address,
            net_amount=net_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            nominal_code=nominal_code,
            description=description,
            raw_text=text,
            pdf_path=str(pdf_path),
        )

        self._validate_required_fields(invoice)

        return invoice

    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number."""
        # Pattern: "Invoice\n# 28564" or "Invoice # 28564"
        match = re.search(r"Invoice[^\d]*#?\s*(\d+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def _extract_po_number(self, text: str) -> str:
        """
        Extract PO number.

        CJL PO numbers can be in format:
        - "110075/CJL316" (extract CJL316)
        - "CJL316"
        """
        # Pattern: "P.O.# : 110075/CJL316" or similar
        match = re.search(r"P\.O\.#?\s*:?\s*(?:\d+/)?(CJL\d{3})", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Fallback: look for CJL followed by 3 digits
        match = re.search(r"(CJL\d{3})", text, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return ""

    def _extract_invoice_date(self, text: str) -> Optional[datetime]:
        """Extract invoice date."""
        # Pattern: "Invoice Date : 12 May 2025"
        match = re.search(
            r"Invoice Date\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})", text, re.IGNORECASE
        )
        if match:
            date_str = match.group(1)
            return self.date_parser.parse_date(date_str)
        return None

    def _extract_store_info(self, text: str) -> tuple[str, str]:
        """
        Extract store location and address.

        Returns:
            Tuple of (store_location, store_address)
        """
        # Pattern: "Subject :\n<store info>"
        match = re.search(
            r"Subject\s*:(.*?)(?:#\s*Item|$)", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            subject_text = match.group(1).strip()

            # Clean up multi-line subject
            lines = [line.strip() for line in subject_text.split("\n") if line.strip()]

            # Last significant line is usually the store location
            if lines:
                store_location = lines[-1]  # e.g., "Portsmouth"
                store_address = " ".join(lines)
                return store_location, store_address

        return "", ""

    def _extract_amounts(
        self, text: str
    ) -> tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Extract net amount, VAT, and total.

        Returns:
            Tuple of (net_amount, vat_amount, total_amount)
        """
        net_amount = None
        vat_amount = None
        total_amount = None

        # Extract Sub Total (net)
        # Pattern: "Sub Total 518.00"
        match = re.search(r"Sub Total\s+([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            net_amount = self.amount_parser.parse_amount(match.group(1))

        # Extract VAT
        # Pattern: "Standard Rate (20%) 103.60"
        match = re.search(r"Standard Rate[^0-9]+([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            vat_amount = self.amount_parser.parse_amount(match.group(1))

        # Extract total
        # Pattern: "Total £621.60"
        match = re.search(r"Total\s+£([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            total_amount = self.amount_parser.parse_amount(match.group(1))

        # If VAT not found, calculate it
        if net_amount and total_amount and not vat_amount:
            vat_amount = self.amount_parser.parse_vat(total_amount, net_amount)

        # If total not found, calculate it
        if net_amount and vat_amount and not total_amount:
            total_amount = self.amount_parser.calculate_total(net_amount, vat_amount)

        return net_amount, vat_amount, total_amount

    def _extract_description(self, text: str) -> str:
        """Extract works description from the item description."""
        # Pattern: "# Item & Description ... <description>"
        match = re.search(
            r"Item & Description.*?\d+\s+(.+?)\s+\d+\.\d+\s+\d+\.\d+",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            description = match.group(1).strip()
            # Clean up multi-line description
            description = " ".join(description.split())
            return description[:500]  # Limit length

        # Fallback: use Subject if item description not found
        match = re.search(
            r"Subject\s*:(.*?)(?:#\s*Item|$)", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            description = match.group(1).strip()
            description = " ".join(description.split())
            return description[:500]

        return ""
