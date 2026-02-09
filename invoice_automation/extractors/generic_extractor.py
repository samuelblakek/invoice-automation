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

    # Known PO number patterns — values that look like internal PO references
    PO_PATTERNS = [
        r'OT\d{3,4}',
        r'SM\d{3,4}',
        r'ORD\d{3,4}',
        r'PO\d{4,5}',
        r'PS\d{4,12}',
        r'CJL\d{3}',
        r'AA\d{4}',
        r'APS\d{3,4}',
        r'ER\d{2}/\d{5}',
    ]

    # Values that are clearly NOT PO numbers
    PO_REJECT_PATTERNS = [
        r'^[A-Z][a-z]+\s+[A-Z][a-z]+',  # Person names like "Sam Boyle"
        r'REPLACEMENT',
        r'E-?MAIL',
        r'CALLED\s+THROUGH',
        r'^[A-Z]{1,2}$',  # Single/double letters like "P", "PO"
    ]

    def extract(self, pdf_path: Path) -> Invoice:
        """Extract invoice data using generic patterns."""
        text = self._extract_text(pdf_path)

        invoice_number = self._extract_invoice_number(text, pdf_path.name)
        po_number = self._extract_po_number(text)

        if not invoice_number:
            raise PDFExtractionError(f"Could not extract invoice number from {pdf_path.name}")

        # Extract date
        invoice_date = self._extract_date(text)

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
        store_location = self._extract_store_location(text) or ""

        # Try to extract nominal code
        nominal_code = self.string_matcher.extract_nominal_code(text) or "7820"

        # Extract description
        description = self._extract_description(text)

        # Determine supplier
        supplier_name = self._identify_supplier(text, pdf_path.name)
        supplier_type = self._identify_supplier_type(text, pdf_path.name)

        invoice = Invoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            supplier_name=supplier_name,
            supplier_type=supplier_type,
            po_number=po_number,
            store_location=store_location,
            store_address="",
            net_amount=net_amount or Decimal('0'),
            vat_amount=vat_amount or Decimal('0'),
            total_amount=total_amount or Decimal('0'),
            nominal_code=nominal_code,
            description=description,
            raw_text=text,
            pdf_path=str(pdf_path)
        )

        return invoice

    def _extract_invoice_number(self, text: str, filename: str) -> str:
        """Extract invoice number using multiple patterns."""
        patterns = [
            # "Invoice No 577608" or "Invoice No. 577608"
            r'Invoice\s+No\.?\s+(\S+)',
            # "Invoice Number :INV29453" (with colon+space)
            r'Invoice\s+Number\s*:\s*(\S+)',
            # "Invoice Number SI-3276"
            r'Invoice\s+Number\s+([A-Z0-9][\w-]+)',
            # "INVOICE 3771211383" or "INVOICE 37712/1383"
            r'INVOICE\s+(\d[\d/.]+)',
            # "Invoice #12345" or "Invoice #: 12345"
            r'Invoice\s+#:?\s*(\S+)',
            # "INV#12345"
            r'INV\s*#?\s*([A-Z0-9]+)',
            # "Invoice No: 28439487"
            r'Invoice\s+No\s*:\s*(\S+)',
            # Compco format: "Ref 0000031483" or "Doc No. 0000031483"
            r'Ref\s+(\d{7,})',
            r'Doc\s+No\.\s+(\d{7,})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_num = match.group(1).strip()
                # Clean up: remove trailing punctuation
                inv_num = inv_num.rstrip('.,;:')
                # Validate: must have at least some digits or be alphanumeric
                if re.search(r'\d', inv_num) and len(inv_num) >= 2:
                    return inv_num

        # Try filename-based extraction as last resort
        # "INV29453" in filename
        match = re.search(r'INV(\d+)', filename, re.IGNORECASE)
        if match:
            return f"INV{match.group(1)}"

        # "PSI577608" → "577608"
        match = re.search(r'PSI(\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1)

        return ""

    def _extract_po_number(self, text: str) -> str:
        """Extract PO number with validation."""
        # Strategy 1: Look for PO reference fields with the actual PO after them
        po_field_patterns = [
            # "P.O. OT0363" → extract "OT0363" (the part after P.O.)
            r'P\.?O\.?\s+([A-Z]{2,4}\d{3,6})',
            # "Order Number: PO54047"
            r'Order\s+(?:Number|No\.?)\s*:?\s*(PO\d{4,6})',
            r'Order\s+(?:Number|No\.?)\s*:?\s*([A-Z]{2,4}\d{3,6})',
            # "Clients Ord Ref. : Called through" — skip (handled by reject)
            # Compco format: "Order No./Job ER22/10808"
            r'Order\s+No\./Job\s+([A-Z0-9/]+)',
        ]

        for pattern in po_field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if self._is_valid_po(candidate):
                    return candidate

        # Strategy 2: Look for known PO patterns anywhere in text
        for po_pattern in self.PO_PATTERNS:
            match = re.search(po_pattern, text)
            if match:
                return match.group(0)

        # Strategy 3: Generic PO/Order field extraction (with validation)
        generic_patterns = [
            r'(?:PO|P\.O\.)\s+(?:No\.?|#|Number)?\s*:?\s*([A-Z0-9/]+)',
            r'Order\s+(?:No\.?|#|Number)\s*:?\s*([A-Z0-9/]+)',
            r'Purchase\s+Order\s*:?\s*([A-Z0-9/]+)',
        ]

        for pattern in generic_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if self._is_valid_po(candidate):
                    return candidate

        # No PO found — return empty string (PO is now optional)
        return ""

    def _is_valid_po(self, candidate: str) -> bool:
        """Check if a candidate string is a valid PO number (not a name/description)."""
        if not candidate or len(candidate) < 2:
            return False

        # Reject known non-PO patterns
        for reject_pattern in self.PO_REJECT_PATTERNS:
            if re.match(reject_pattern, candidate, re.IGNORECASE):
                return False

        # Must contain at least one digit
        if not re.search(r'\d', candidate):
            return False

        return True

    def _extract_date(self, text: str) -> object:
        """Extract invoice date."""
        date_patterns = [
            r'(?:Invoice|Tax)\s*(?:Date|Point)[/\s]*(?:Date)?\s*:?\s*(\d{1,2}[\s/-]\w+[\s/-]\d{2,4})',
            r'Date\s*:?\s*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'Invoice\s+Date\s+(\d{1,2}/\d{1,2}/\d{2,4})',
            r'Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = self.date_parser.parse_date(match.group(1))
                if result:
                    return result
        return None

    def _extract_net_amount(self, text: str) -> Decimal:
        """Extract net/subtotal amount."""
        patterns = [
            # "GOODS TOTAL 69.90" (Sunbelt)
            r'GOODS\s+TOTAL\s+£?\s*([\d,]+\.?\d*)',
            # "Total Net 218.00" (Metro Security)
            r'Total\s+Net\s+£?\s*([\d,]+\.?\d*)',
            # "Job Totals £132.30" (Store Maintenance)
            r'Job\s+Totals?\s+£?\s*([\d,]+\.?\d*)',
            # "Invoice Totals\n£132.30 £26.46 £158.76" — first amount is net
            r'Invoice\s+Totals?\s*\n\s*£?([\d,]+\.\d{2})',
            # Compco format: "NET 95.00" (after VAT Analysis section)
            r'VAT Analysis.*?NET\s+([\d,]+\.?\d*)',
            # Standard formats
            r'NET\s+TOTAL\s+£?\s*([\d,]+\.?\d*)',
            r'Sub\s*Total\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Subtotal\s*:?\s*£?\s*([\d,]+\.?\d*)',
            r'Total\s+(?:ex|before|excl)\w*\s+VAT\s*:?\s*£?\s*([\d,]+\.?\d*)',
            # "Total Net" with currency
            r'Total\s+Net\s*:?\s*£?\s*([\d,]+\.?\d*)',
            # "Net" standalone with amount (broad — last resort)
            r'\bNet\b\s*:?\s*£?\s*([\d,]+\.?\d*)',
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
        """Extract VAT amount, avoiding VAT registration numbers."""
        patterns = [
            # "VAT TOTAL 13.98" on same line (Sunbelt)
            r'VAT\s+TOTAL\s+£?([\d,]+\.\d{2})',
            # "VAT at 20.00% 43.60" (Metro Security)
            r'VAT\s+(?:at|@)\s+[\d.]+%\s+£?([\d,]+\.\d{2})',
            # "Total VAT 164.00" (ILUX)
            r'Total\s+VAT\s+£?([\d,]+\.\d{2})',
            # "No VAT 26.27" (LampShopOnline — "No VAT" means the VAT amount)
            r'No\s+VAT\s+£?([\d,]+\.\d{2})',
            # "£26.46" preceded by VAT rate on same line: "20.00% £26.46"
            r'20\.00%\s+£([\d,]+\.\d{2})',
            # "VAT 202.00" on same line — must have decimal digits
            r'\bVAT\b\s+£?([\d,]+\.\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal('0'):
                    # Sanity check: VAT should be reasonable (not a reg number)
                    if amount < Decimal('100000'):
                        return amount

        return Decimal('0')

    def _extract_total_amount(self, text: str) -> Decimal:
        """Extract total amount."""
        patterns = [
            # "INVOICE TOTAL 83.88" (Sunbelt)
            r'INVOICE\s+TOTAL\s+£?\s*([\d,]+\.\d{2})',
            # "Invoice Total £ 261.60" (Metro Security)
            r'Invoice\s+Total\s+£?\s*([\d,]+\.\d{2})',
            # "TOTAL £984.00" (ILUX)
            r'\bTOTAL\s+£\s*([\d,]+\.\d{2})',
            # "Total Inc VAT 157.61" (LampShopOnline)
            r'Total\s+Inc\s+VAT\s+£?\s*([\d,]+\.\d{2})',
            # "Invoice Totals\n£132.30 £26.46 £158.76" — last amount is total
            r'Invoice\s+Totals?\s*\n\s*£?[\d,]+\.\d{2}\s+£?[\d,]+\.\d{2}\s+£?([\d,]+\.\d{2})',
            # "Job Totals £132.30 £26.46 £158.76" — last amount is total
            r'Job\s+Totals?\s+£?[\d,]+\.\d{2}\s+£?[\d,]+\.\d{2}\s+£?([\d,]+\.\d{2})',
            # Standard formats
            r'(?:Grand\s+)?Total\s+(?:Amount|Due|Payable)?\s*:?\s*£?\s*([\d,]+\.\d{2})',
            r'Amount\s+Due\s*:?\s*£?\s*([\d,]+\.\d{2})',
            r'Balance\s+Due\s*:?\s*£?\s*([\d,]+\.\d{2})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal('0'):
                    return amount
        return Decimal('0')

    # Menkind HQ / billing address — never a store location
    _BILLING_CITIES = {'dorking'}

    def _extract_store_location(self, text: str) -> str:
        """Extract store/site name from invoice text using generic patterns."""
        # 1. Explicit "Site Address" section — last line is usually the city
        match = re.search(
            r'SITE\s+ADDRESS:\s*(.*?)(?:Site\s+Ref|Order\s+No|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        if match:
            lines = [l.strip() for l in match.group(1).strip().split('\n') if l.strip()]
            if lines:
                city = re.sub(r'[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}', '', lines[-1]).strip()
                if city and len(city) > 2 and not city.lower().startswith('unit'):
                    return city

        # 2. Explicit "Site Name" field — strip "Menkind" prefix if present
        match = re.search(r'Site\s+Name\s*:\s*(?:Menkind\s+)?(\S+)', text, re.IGNORECASE)
        if match:
            store = match.group(1).strip()
            if store and len(store) > 2:
                return store

        # 3. "X Shopping Centre" anywhere in text — extract X
        match = re.search(r'(\w+)\s+Shopping\s+Centr', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 4. "Units XX-XX, Location" in description text (OCR may read l for 1)
        match = re.search(r'Units?\s+[\d\w]+-\d+\s*,\s*(\w+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 5. "Reference <name> - <location>" field
        match = re.search(r'Reference\s+\w+\s*-\s*(\w+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # 6. City, Postcode pairs — pick first UNIQUE one that isn't the billing address
        #    If a city appears multiple times it's likely the supplier's address, not the store
        city_matches = re.findall(
            r'([A-Z][a-z]{2,}),\s*[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}', text
        )
        city_counts = {}
        for c in city_matches:
            city_counts[c] = city_counts.get(c, 0) + 1
        delivery_cities = [
            c for c in city_matches
            if c.lower() not in self._BILLING_CITIES and city_counts[c] == 1
        ]
        if delivery_cities:
            return delivery_cities[0]

        # 7. "Menkind <StoreName>" — skip company words
        match = re.search(r'Menkind\s+(\w+)', text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            skip = {'limited', 'ltd', 'contract', 'the', 'atrium', 'business'}
            if candidate.lower() not in skip:
                return candidate

        # 8. Compco-style embedded reference
        match = re.search(r'##VAR37\s+(.+?)##', text)
        if match:
            return match.group(1).strip()

        # Fallback: use StringMatcher
        return self.string_matcher.extract_store_name(text) or ""

    def _extract_description(self, text: str) -> str:
        """Extract work description."""
        patterns = [
            # "Description" or "Description:" followed by text
            r'Description\s*:\s*(.*?)(?:\n\n|Total|Visits|$)',
            r'Work\s+Description\s*:?\s*(.*?)(?:\n\n|Total|$)',
            r'Details\s*:?\s*(.*?)(?:\n\n|Total|$)',
            # Compco format
            r'Line\s+Item.*?Description.*?\n.*?\n\d+\s+(.+?)(?:\d+\.\d{2}|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                desc = re.sub(r'##\w+.*?##', '', desc)
                desc = ' '.join(desc.split())
                if desc and len(desc) > 5:
                    return desc[:500]
        return ""

    def _identify_supplier(self, text: str, filename: str) -> str:
        """Identify supplier name from text or filename."""
        text_lower = text.lower()
        filename_lower = filename.lower()

        if 'sunbelt' in text_lower or 'sunbelt' in filename_lower:
            return "Sunbelt Rentals"
        if 'maxwell jones' in text_lower or 'maxwelljones' in text_lower:
            return "Maxwell Jones"
        if 'metro security' in text_lower:
            return "Metro Security"
        if 'store maintenance' in text_lower and 'reactive on call' in text_lower:
            return "Store Maintenance / Reactive on Call FM"
        if 'store maintenance' in text_lower:
            return "Store Maintenance"
        if 'reactive on call' in text_lower:
            return "Reactive on Call FM"
        if 'lampshoponline' in text_lower or 'lampshop' in text_lower:
            return "LampShopOnline"
        if 'ilux' in text_lower:
            return "ILUX Lighting"
        if 'compco' in text_lower or 'compco' in filename_lower:
            return "Compco Fire Systems"
        if 'aura' in text_lower:
            return "Aura Air Conditioning"
        if 'metsafe' in text_lower:
            return "MetSafe"

        return "Unknown Supplier"

    def _identify_supplier_type(self, text: str, filename: str) -> str:
        """Identify supplier type code for sheet routing."""
        text_lower = text.lower()
        filename_lower = filename.lower()

        if 'sunbelt' in text_lower or 'sunbelt' in filename_lower:
            return "SUNBELT"
        if 'maxwell jones' in text_lower or 'maxwelljones' in text_lower:
            return "MAXWELL_JONES"
        if 'metro security' in text_lower:
            return "METRO_SECURITY"
        if 'store maintenance' in text_lower or 'reactive on call' in text_lower:
            return "STORE_MAINTENANCE"
        if 'lampshoponline' in text_lower or 'lampshop' in text_lower:
            return "LAMPSHOP"
        if 'ilux' in text_lower:
            return "ILUX"
        if 'compco' in text_lower or 'compco' in filename_lower:
            return "COMPCO"
        if 'aura' in text_lower:
            return "AURA"

        return "OTHER"
