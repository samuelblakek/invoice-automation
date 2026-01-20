"""
Generic invoice extractor (fallback for unknown suppliers).
"""
from pathlib import Path
from decimal import Decimal
import re

from .base_extractor import BaseExtractor, PDFExtractionError
from ..models import Invoice


class GenericExtractor(BaseExtractor):
    """Generic extractor for invoices from unknown suppliers."""

    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data using generic patterns.

        Attempts to find common invoice fields using flexible patterns.

        Args:
            pdf_path: Path to the invoice PDF

        Returns:
            Invoice object with extracted data
        """
        text = self._extract_text(pdf_path)

        # Try multiple patterns for invoice number
        invoice_number = (
            # Compco format: "Ref 0000031483" or "Doc No. 0000031483"
            self._find_pattern(text, r'Ref\s+(\d{7,})', re.IGNORECASE) or
            self._find_pattern(text, r'Doc\s+No\.\s+(\d{7,})', re.IGNORECASE) or
            # Standard formats
            self._find_pattern(text, r'Invoice\s+(?:No\.?|#|Number)\s*:?\s*([A-Z0-9]+)', re.IGNORECASE) or
            self._find_pattern(text, r'INV\s*#?\s*([A-Z0-9]+)', re.IGNORECASE) or
            ""
        )

        po_number = (
            # Compco format: "Order No./Job ER22/10808"
            self._find_pattern(text, r'Order\s+No\./Job\s+([A-Z0-9/]+)', re.IGNORECASE) or
            # Standard formats
            self._find_pattern(text, r'(?:PO|P\.O\.|Order)\s+(?:No\.?|#|Number)?\s*:?\s*([A-Z0-9/]+)', re.IGNORECASE) or
            self.string_matcher.extract_po_number(text) or
            ""
        )

        if not invoice_number:
            raise PDFExtractionError(f"Could not extract invoice number from {pdf_path.name}")

        # Extract date
        invoice_date = None
        date_match = re.search(r'(?:Invoice|Date)\s+(?:Date)?\s*:?\s*(\d{1,2}[/-]\s*\w+\s*[/-]\s*\d{2,4})', text, re.IGNORECASE)
        if date_match:
            invoice_date = self.date_parser.parse_date(date_match.group(1))

        # Extract amounts
        net_amount = self._extract_net_amount(text)
        vat_amount = self._extract_vat_amount(text)
        total_amount = self._extract_total_amount(text)

        # Calculate missing amounts if possible
        if not net_amount and total_amount and vat_amount:
            net_amount = total_amount - vat_amount
        elif not vat_amount and total_amount and net_amount:
            vat_amount = total_amount - net_amount
        elif not total_amount and net_amount and vat_amount:
            total_amount = net_amount + vat_amount

        # Extract store/site info
        store_location = self._extract_store_from_address(text) or self.string_matcher.extract_store_name(text) or ""
        store_address = ""

        # Try to extract nominal code
        nominal_code = self.string_matcher.extract_nominal_code(text) or "7820"

        # Extract description
        description = self._extract_description(text)

        # Determine supplier
        supplier_name = self._identify_supplier(text, pdf_path.name)

        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name=supplier_name,
            supplier_type="OTHER",
            po_number=po_number,
            store_location=store_location,
            store_address=store_address,
            net_amount=net_amount or Decimal('0'),
            vat_amount=vat_amount or Decimal('0'),
            total_amount=total_amount or Decimal('0'),
            nominal_code=nominal_code,
            description=description,
            raw_text=text,
            pdf_path=str(pdf_path)
        )

        return invoice

    def _extract_net_amount(self, text: str) -> Decimal:
        """Extract net/subtotal amount."""
        patterns = [
            # Compco format: "NET 95.00" (after VAT Analysis section)
            r'VAT Analysis.*?NET\s+([\d,]+\.?\d*)',
            # Standard formats
            r'NET\s+TOTAL\s+£\s*([\d,]+\.?\d*)',
            r'Sub\s*Total\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Subtotal\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Net\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Total\s+(?:ex|before)\s+VAT\s*:?\s*£?\s*([\d,]+\.?\d*)',
            # Look for "NET" followed by amount (broader pattern)
            r'\bNET\b\s+([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal('0'):
                    return amount
        return Decimal('0')

    def _extract_vat_amount(self, text: str) -> Decimal:
        """Extract VAT amount."""
        match = re.search(r'VAT[^£\d]*(£?\s*[\d,]+\.?\d*)', text, re.IGNORECASE)
        if match:
            return self.amount_parser.parse_amount(match.group(1)) or Decimal('0')
        return Decimal('0')

    def _extract_total_amount(self, text: str) -> Decimal:
        """Extract total amount."""
        patterns = [
            r'(?:Grand\s+)?Total\s+(?:Amount|Due|Payable)?\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Amount\s+Due\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Balance\s+Due\s*:?\s*£?\s*([\d,]+\.?\d*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.amount_parser.parse_amount(match.group(1)) or Decimal('0')
        return Decimal('0')

    def _extract_description(self, text: str) -> str:
        """Extract work description."""
        patterns = [
            # Compco format: Line item description
            r'Line\s+Item.*?Description.*?\n.*?\n\d+\s+(.+?)(?:\d+\.\d{2}|$)',
            # Standard formats
            r'Description\s*:?\s*(.*?)(?:\n\n|Total|$)',
            r'Work\s+Description\s*:?\s*(.*?)(?:\n\n|Total|$)',
            r'Details\s*:?\s*(.*?)(?:\n\n|Total|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                # Remove metadata tags (Compco has ##VAR## tags)
                desc = re.sub(r'##\w+.*?##', '', desc)
                desc = ' '.join(desc.split())
                if desc and len(desc) > 5:  # Must have meaningful content
                    return desc[:500]
        return ""

    def _extract_store_from_address(self, text: str) -> str:
        """Extract store name from delivery/install address."""
        # Compco format: Look for "##VAR37 UNIT 104 BRAEHEAD CENTRE##"
        match = re.search(r'##VAR37\s+(.+?)##', text)
        if match:
            return match.group(1).strip()

        # Standard format: Look for "Menkind" followed by store name
        match = re.search(r'Menkind.*?REF:\s*([A-Z\s]+)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        return ""

    def _identify_supplier(self, text: str, filename: str) -> str:
        """Identify supplier from text or filename."""
        # Check filename first
        filename_lower = filename.lower()
        if 'compco' in filename_lower:
            return "Compco Fire Systems"

        # Check text
        text_lower = text.lower()
        if 'compco' in text_lower:
            return "Compco Fire Systems"
        elif 'aura' in text_lower:
            return "Aura Air Conditioning"

        return "Unknown Supplier"
