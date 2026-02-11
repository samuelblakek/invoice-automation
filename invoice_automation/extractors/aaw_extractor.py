"""
AAW National invoice extractor.
"""

from pathlib import Path
import re

from .base_extractor import BaseExtractor, PDFExtractionError
from ..models import Invoice


class AAWExtractor(BaseExtractor):
    """Extractor for AAW National (PANDA) invoices."""

    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data from AAW National PDF.

        Expected format:
        - Invoice No: 5002746
        - Order No: PS0301111817
        - Date: 08 May 2025
        - Site: Menkind Limited - Maidstone - Address
        - Total: £116.50 (net before VAT)
        - VAT @ 20.00%: £23.30
        - This Invoice: £139.80 (total with VAT)

        Args:
            pdf_path: Path to the AAW invoice PDF

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
                "Could not extract invoice number from AAW invoice"
            )

        # Extract PO number
        po_number = self._extract_po_number(text)
        if not po_number:
            raise PDFExtractionError("Could not extract PO number from AAW invoice")

        # Extract date
        invoice_date = self._extract_invoice_date(text)

        # Extract site/store information
        store_location, store_address = self._extract_store_info(text)

        # Extract amounts
        net_amount, vat_amount, total_amount = self._extract_amounts(text)
        if not net_amount:
            raise PDFExtractionError("Could not extract amounts from AAW invoice")

        # Extract description
        description = self._extract_description(text)

        nominal_code = ""

        # Create invoice object
        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name="AAW National Shutters Ltd",
            supplier_type="AAW",
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
            extracted_fields={
                "works_completed": self._extract_works_completed(text),
            },
        )

        self._validate_required_fields(invoice)

        return invoice

    def _extract_invoice_number(self, text: str) -> str:
        """Extract invoice number."""
        # Pattern: "Invoice No 5002746" or "Invoice No: 5002746"
        match = re.search(r"Invoice\s+No[:\s]+(\d+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""

    def _extract_po_number(self, text: str) -> str:
        """Extract PO/Order number."""
        # Pattern: "Order No PS0301111817" or "Order No: PS0301111817"
        match = re.search(r"Order\s+No[:\s]+(PS\d{10,12})", text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Fallback: look for PS followed by digits
        match = re.search(r"(PS\d{10,12})", text)
        if match:
            return match.group(1)

        return ""

    def _extract_invoice_date(self, text: str) -> any:
        """Extract invoice date."""
        # Pattern: "Date 08 May 2025" or "Customer Date 08 May 2025"
        match = re.search(r"Date\s+(\d{1,2}\s+\w+\s+\d{4})", text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            return self.date_parser.parse_date(date_str)
        return None

    def _extract_store_info(self, text: str) -> tuple:
        """
        Extract store location and address.

        Returns:
            Tuple of (store_location, store_address)
        """
        # Pattern: "Site\nMenkind Limited - Maidstone - Address"
        match = re.search(
            r"Site\s*(.*?)(?:Works Description:|$)", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            site_text = match.group(1).strip()

            # Extract store name from pattern "Menkind Limited - StoreName - Address"
            store_match = re.match(
                r"Menkind Limited\s*-\s*([^-]+)", site_text, re.IGNORECASE
            )
            if store_match:
                store_location = store_match.group(1).strip()
                # Clean up multi-line address
                store_address = " ".join(site_text.split())
                return store_location, store_address

        return "", ""

    def _extract_amounts(self, text: str) -> tuple:
        """
        Extract net amount, VAT, and total.

        Returns:
            Tuple of (net_amount, vat_amount, total_amount)
        """
        net_amount = None
        vat_amount = None
        total_amount = None

        # Extract Total (net before VAT)
        # Pattern: "Total £ 116.50" or "Total £116.50"
        match = re.search(r"Total\s+£\s*([\d,]+\.?\d*)", text)
        if match:
            net_amount = self.amount_parser.parse_amount(match.group(1))

        # Extract VAT
        # Pattern: "VAT @ 20.00% £ 23.30"
        match = re.search(r"VAT[^£]*£\s*([\d,]+\.?\d*)", text)
        if match:
            vat_amount = self.amount_parser.parse_amount(match.group(1))

        # Extract total with VAT
        # Pattern: "This Invoice £ 139.80"
        match = re.search(r"This Invoice\s+£\s*([\d,]+\.?\d*)", text)
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
        """Extract works description."""
        # Pattern: "Works Description:\n<description>\nWorks Completed:"
        match = re.search(
            r"Works Description:(.*?)Works Completed:", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            description = match.group(1).strip()
            # Clean up multi-line description
            description = " ".join(description.split())
            return description[:500]  # Limit length
        return ""

    def _extract_works_completed(self, text: str) -> any:
        """Extract works completed date."""
        # Pattern: "Works Completed: 07 May 2025"
        match = re.search(
            r"Works Completed:\s*(\d{1,2}\s+\w+\s+\d{4})", text, re.IGNORECASE
        )
        if match:
            date_str = match.group(1)
            return self.date_parser.parse_date(date_str)
        return None
