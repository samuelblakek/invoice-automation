"""
Amazon Business invoice extractor.
"""

from pathlib import Path
from decimal import Decimal
import re

from .base_extractor import BaseExtractor, PDFExtractionError
from ..models import Invoice


class AmazonExtractor(BaseExtractor):
    """Extractor for Amazon Business invoices."""

    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data from Amazon Business PDF.

        Expected format:
        - Invoice #: GB5Q1QGABEY
        - Invoice date: 3 April 2025
        - PO #: ORD816 (Leicester 7820)
        - Delivery address: Menkind Leicester
        - Total payable: £23.96

        Args:
            pdf_path: Path to the Amazon invoice PDF

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
                "Could not extract invoice number from Amazon invoice"
            )

        # Extract PO number
        po_number, _nominal_code, store_from_po = self._extract_po_and_code(text)
        nominal_code = ""
        if not po_number:
            raise PDFExtractionError("Could not extract PO number from Amazon invoice")

        # Extract date
        invoice_date = self._extract_invoice_date(text)

        # Extract store information
        store_location, store_address = self._extract_store_info(text, store_from_po)

        # Extract amounts (Amazon invoices often require looking at item details)
        net_amount, vat_amount, total_amount = self._extract_amounts(text)
        if not total_amount:
            raise PDFExtractionError("Could not extract amounts from Amazon invoice")

        # Extract description (from order items - may be on next page)
        description = self._extract_description(text)

        # Create invoice object
        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name="Amazon Business",
            supplier_type="AMAZON",
            po_number=po_number,
            store_location=store_location,
            store_address=store_address,
            net_amount=net_amount or Decimal("0"),
            vat_amount=vat_amount or Decimal("0"),
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
        # Pattern: "Invoice # GB5Q1QGABEY" or "Invoice #\nGB5Q1QGABEY"
        match = re.search(r"Invoice\s*#\s*\n?\s*([A-Z0-9]{10,})", text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Fallback: look for alphanumeric code after "Invoice #"
        match = re.search(r"Invoice\s*#\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if match:
            inv_num = match.group(1)
            # Filter out common words that aren't invoice numbers
            if inv_num.upper() not in ["DATE", "NUMBER", "NO", "INVOICE"]:
                return inv_num

        return ""

    def _extract_po_and_code(self, text: str) -> tuple:
        """
        Extract PO number and nominal code from PO field.

        Amazon PO format: "ORD816 (Leicester 7820)"
        Extract: PO="ORD816", nominal_code="7820", store="Leicester"

        Returns:
            Tuple of (po_number, nominal_code, store_name)
        """
        # Pattern: "PO # ORD816 (Leicester 7820)"
        match = re.search(
            r"PO #?\s*(ORD\d{3,4})\s*\(([^)]+?)\s*(\d{4})\)", text, re.IGNORECASE
        )
        if match:
            po_number = match.group(1).upper()
            store_name = match.group(2).strip()
            nominal_code = match.group(3)
            return po_number, nominal_code, store_name

        # Fallback: just get PO number
        match = re.search(r"PO #?\s*(ORD\d{3,4})", text, re.IGNORECASE)
        if match:
            return match.group(1).upper(), None, None

        return "", None, None

    def _extract_invoice_date(self, text: str) -> any:
        """Extract invoice date."""
        # Pattern: "Invoice date 3 April 2025"
        match = re.search(
            r"Invoice date\s*(\d{1,2}\s+\w+\s+\d{4})", text, re.IGNORECASE
        )
        if match:
            date_str = match.group(1)
            return self.date_parser.parse_date(date_str)
        return None

    def _extract_store_info(self, text: str, store_from_po: str = None) -> tuple:
        """
        Extract store location and address.

        Returns:
            Tuple of (store_location, store_address)
        """
        store_location = store_from_po or ""

        # Pattern: "Delivery address\n...\nMenkind\nLeicester..."
        match = re.search(
            r"Delivery address(.*?)(?:Sold by|$)", text, re.IGNORECASE | re.DOTALL
        )
        if match:
            delivery_text = match.group(1).strip()
            lines = [line.strip() for line in delivery_text.split("\n") if line.strip()]

            # Find lines with store info
            for line in lines:
                if "menkind" in line.lower():
                    # Next line might be store location
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        potential_store = lines[idx + 1]
                        # Check if it's a store name (not an address line)
                        if (
                            not re.match(r"\d+", potential_store)
                            and len(potential_store) < 30
                        ):
                            if not store_location:
                                store_location = potential_store

            store_address = " ".join(lines)
            return store_location, store_address

        return store_location, ""

    def _extract_amounts(self, text: str) -> tuple:
        """
        Extract net amount, VAT, and total.

        Amazon invoices show "Total payable" on page 1 (total with VAT).
        Page 2 has detailed breakdown with "Item subtotal excl. VAT" and VAT subtotal.

        Returns:
            Tuple of (net_amount, vat_amount, total_amount)
        """
        net_amount = None
        vat_amount = None
        total_amount = None

        # Extract Total payable (includes VAT)
        match = re.search(r"Total payable\s+£([\d,]+\.?\d*)", text, re.IGNORECASE)
        if match:
            total_amount = self.amount_parser.parse_amount(match.group(1))

        # Look for the detailed breakdown (usually on page 2)
        # Pattern: "Total £19.96 £4.00" where first is net, second is VAT
        # or "Item subtotal excl. VAT" section
        match = re.search(
            r"Total\s+£([\d,]+\.?\d*)\s+£([\d,]+\.?\d*)", text, re.IGNORECASE
        )
        if match:
            net_amount = self.amount_parser.parse_amount(match.group(1))
            vat_amount = self.amount_parser.parse_amount(match.group(2))

        # Alternative: look for VAT rate table
        # Pattern: "20.0 % £19.96 £4.00"
        if not net_amount:
            match = re.search(
                r"20\.0\s*%\s+£([\d,]+\.?\d*)\s+£([\d,]+\.?\d*)", text, re.IGNORECASE
            )
            if match:
                net_amount = self.amount_parser.parse_amount(match.group(1))
                vat_amount = self.amount_parser.parse_amount(match.group(2))

        # Calculate missing values if we only have total
        if total_amount and not net_amount:
            # Assume 20% VAT
            net_amount = total_amount / Decimal("1.20")
            vat_amount = total_amount - net_amount

        return net_amount, vat_amount, total_amount

    def _extract_description(self, text: str) -> str:
        """Extract order description."""
        # Look for product names in the text
        # Pattern: Item descriptions usually after "Order information"
        match = re.search(
            r"Order information(.*?)(?:Remit to|Page \d)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            order_info = match.group(1).strip()
            # Clean up
            description = " ".join(order_info.split())
            return description[:500]

        return "Amazon Business Order"
