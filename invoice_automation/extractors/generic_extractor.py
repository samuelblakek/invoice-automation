"""
Generic invoice extractor (fallback for unknown suppliers).
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
import re

from .base_extractor import BaseExtractor, PDFExtractionError
from ..models import Invoice
from ..utils.supplier_registry import identify_supplier as _identify_supplier_registry


class GenericExtractor(BaseExtractor):
    """Generic extractor for invoices from unknown suppliers."""

    # Known PO number patterns — values that look like internal PO references
    PO_PATTERNS = [
        r"OT\d{3,4}",
        r"SM\d{3,4}",
        r"ORD\d{3,4}",
        r"PO\d{4,5}",
        r"PS\d{4,12}",
        r"CJL\d{3}",
        r"AA\d{4}",
        r"APS\d{3,4}",
        r"ER\d{2}/\d{5}",
    ]

    # Values that are clearly NOT PO numbers
    PO_REJECT_PATTERNS = [
        r"^[A-Z][a-z]+\s+[A-Z][a-z]+",  # Person names like "Sam Boyle"
        r"REPLACEMENT",
        r"E-?MAIL",
        r"CALLED\s+THROUGH",
        r"^[A-Z]{1,2}$",  # Single/double letters like "P", "PO"
    ]

    def extract(self, pdf_path: Path) -> Invoice:
        """Extract invoice data using generic patterns."""
        text = self._extract_text(pdf_path)

        invoice_number = self._extract_invoice_number(text, pdf_path.name)
        po_number = self._extract_po_number(text)

        if not invoice_number:
            raise PDFExtractionError(
                f"Could not extract invoice number from {pdf_path.name}"
            )

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

        nominal_code = ""

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
            net_amount=net_amount or Decimal("0"),
            vat_amount=vat_amount or Decimal("0"),
            total_amount=total_amount or Decimal("0"),
            nominal_code=nominal_code,
            description=description,
            raw_text=text,
            pdf_path=str(pdf_path),
        )

        return invoice

    def _extract_invoice_number(self, text: str, filename: str) -> str:
        """Extract invoice number using multiple patterns."""
        patterns = [
            # "Invoice No 577608" or "Invoice No. 577608"
            r"Invoice\s+No\.?\s+(\S+)",
            # "Invoice Number :INV29453" (with colon+space)
            r"Invoice\s+Number\s*:\s*(\S+)",
            # "Invoice Number SI-3276"
            r"Invoice\s+Number\s+([A-Z0-9][\w-]+)",
            # "INVOICE 3771211383" or "INVOICE 37712/1383"
            r"INVOICE\s+(\d[\d/.]+)",
            # "Invoice #12345" or "Invoice #: 12345"
            r"Invoice\s+#:?\s*(\S+)",
            # "INV#12345"
            r"INV\s*#?\s*([A-Z0-9]+)",
            # "Invoice No: 28439487"
            r"Invoice\s+No\s*:\s*(\S+)",
            # Compco format: "Ref 0000031483" or "Doc No. 0000031483"
            r"Ref\s+(\d{7,})",
            r"Doc\s+No\.\s+(\d{7,})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inv_num = match.group(1).strip()
                # Clean up: remove trailing punctuation
                inv_num = inv_num.rstrip(".,;:")
                # Validate: must have at least some digits or be alphanumeric
                if re.search(r"\d", inv_num) and len(inv_num) >= 2:
                    return inv_num

        # Try filename-based extraction as last resort.
        # Handles "INV29453", "INV-10801", "INV_10801", "INV 10801" — the
        # separator between "INV" and the digits is optional. A hyphen or
        # underscore is preserved (e.g. "INV-10801"); whitespace is dropped.
        match = re.search(r"INV([-_ ]?)(\d+)", filename, re.IGNORECASE)
        if match:
            separator = match.group(1).strip()
            return f"INV{separator}{match.group(2)}"

        # "PSI577608" → "577608"
        match = re.search(r"PSI(\d+)", filename, re.IGNORECASE)
        if match:
            return match.group(1)

        return ""

    def _extract_po_number(self, text: str) -> str:
        """Extract PO number with validation."""
        # Strategy 1: Look for PO reference fields with the actual PO after them
        po_field_patterns = [
            # "Order number 123118/OT0402" or "Order number LUX010" — the real PO
            # is the code after an optional "<ticket>/" prefix (Menkind/ILUX format).
            r"Order\s+number\s+(?:\d+/)?([A-Z]{2,4}\d{3,6})",
            # "P.O. OT0363" → extract "OT0363" (the part after P.O.)
            r"P\.?O\.?\s+([A-Z]{2,4}\d{3,6})",
            # "Order Number: PO54047"
            r"Order\s+(?:Number|No\.?)\s*:?\s*(PO\d{4,6})",
            r"Order\s+(?:Number|No\.?)\s*:?\s*([A-Z]{2,4}\d{3,6})",
            # "Clients Ord Ref. : Called through" — skip (handled by reject)
            # Compco format: "Order No./Job ER22/10808"
            r"Order\s+No\./Job\s+([A-Z0-9/]+)",
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
            r"(?:PO|P\.O\.)\s+(?:No\.?|#|Number)?\s*:?\s*([A-Z0-9/]+)",
            r"Order\s+(?:No\.?|#|Number)\s*:?\s*([A-Z0-9/]+)",
            r"Purchase\s+Order\s*:?\s*([A-Z0-9/]+)",
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
        if not re.search(r"\d", candidate):
            return False

        return True

    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract invoice date."""
        date_patterns = [
            r"(?:Invoice|Tax)\s*(?:Date|Point)[/\s]*(?:Date)?\s*:?\s*(\d{1,2}[\s/-]\w+[\s/-]\d{2,4})",
            r"Date\s*:?\s*(\d{1,2}/\d{1,2}/\d{2,4})",
            r"Invoice\s+Date\s+(\d{1,2}/\d{1,2}/\d{2,4})",
            r"Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})",
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
            r"GOODS\s+TOTAL\s+£?\s*([\d,]+\.?\d*)",
            # "Total Net 218.00" (Metro Security)
            r"Total\s+Net\s+£?\s*([\d,]+\.?\d*)",
            # "Job Totals £132.30" (Store Maintenance)
            r"Job\s+Totals?\s+£?\s*([\d,]+\.?\d*)",
            # "Invoice Totals\n£132.30 £26.46 £158.76" — first amount is net
            r"Invoice\s+Totals?\s*\n\s*£?([\d,]+\.\d{2})",
            # Compco format: "NET 95.00" (after VAT Analysis section)
            r"VAT Analysis.*?NET\s+([\d,]+\.?\d*)",
            # Standard formats
            r"NET\s+TOTAL\s+£?\s*([\d,]+\.?\d*)",
            r"Sub\s*Total\s*:?\s*£?\s*([\d,]+\.?\d*)",
            r"Subtotal\s*:?\s*£?\s*([\d,]+\.?\d*)",
            r"Total\s+(?:ex|before|excl)\w*\s+VAT\s*:?\s*£?\s*([\d,]+\.?\d*)",
            # "Total Net" with currency
            r"Total\s+Net\s*:?\s*£?\s*([\d,]+\.?\d*)",
            # "Net" standalone with amount (broad — last resort). Require a
            # decimal so payment terms like "Net 30 days" can't become net=30.
            r"\bNet\b\s*:?\s*£?\s*([\d,]+\.\d{2})",
            # Look for "NET" followed by amount (broader pattern, decimal required)
            r"\bNET\b\s+£?([\d,]+\.\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal("0"):
                    return amount
        return Decimal("0")

    def _extract_vat_amount(self, text: str) -> Decimal:
        """Extract VAT amount, avoiding VAT registration numbers."""
        patterns = [
            # "VAT TOTAL 13.98" on same line (Sunbelt)
            r"VAT\s+TOTAL\s+£?([\d,]+\.\d{2})",
            # "VAT at 20.00% 43.60" (Metro Security)
            r"VAT\s+(?:at|@)\s+[\d.]+%\s+£?([\d,]+\.\d{2})",
            # "Total VAT 164.00" (ILUX older template)
            r"Total\s+VAT\s+£?([\d,]+\.\d{2})",
            # "Total Tax 23.00" (ILUX current template)
            r"Total\s+Tax\s+£?([\d,]+\.\d{2})",
            # "No VAT 26.27" (LampShopOnline — "No VAT" means the VAT amount)
            r"No\s+VAT\s+£?([\d,]+\.\d{2})",
            # "£26.46" preceded by VAT rate on same line: "20.00% £26.46"
            r"20\.00%\s+£([\d,]+\.\d{2})",
            # "VAT 202.00" on same line — must have decimal digits.
            # Negative lookbehinds avoid matching the net line "Total ex VAT
            # 115.00" and its variants ("exc", "excl", "ex.").
            r"(?<!ex )(?<!exc )(?<!excl )(?<!ex\. )\bVAT\b\s+£?([\d,]+\.\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal("0"):
                    # Sanity check: VAT should be reasonable (not a reg number)
                    if amount < Decimal("100000"):
                        return amount

        return Decimal("0")

    def _extract_total_amount(self, text: str) -> Decimal:
        """Extract total amount."""
        patterns = [
            # "INVOICE TOTAL 83.88" (Sunbelt) / "INVOICE TOTAL f.1212.00" — some
            # fonts emit the ASCII "f." for the £ glyph, so accept £ or "f.".
            r"INVOICE\s+TOTAL\s+(?:£|f\.)?\s*([\d,]+\.\d{2})",
            # "Invoice Total £ 261.60" (Metro Security)
            r"Invoice\s+Total\s+(?:£|f\.)?\s*([\d,]+\.\d{2})",
            # "TOTAL £984.00" (ILUX)
            r"\bTOTAL\s+(?:£|f\.)\s*([\d,]+\.\d{2})",
            # "Total Inc VAT 157.61" (LampShopOnline)
            r"Total\s+Inc\s+VAT\s+£?\s*([\d,]+\.\d{2})",
            # "Invoice Totals\n£132.30 £26.46 £158.76" — last amount is total
            r"Invoice\s+Totals?\s*\n\s*£?[\d,]+\.\d{2}\s+£?[\d,]+\.\d{2}\s+£?([\d,]+\.\d{2})",
            # "Job Totals £132.30 £26.46 £158.76" — last amount is total
            r"Job\s+Totals?\s+£?[\d,]+\.\d{2}\s+£?[\d,]+\.\d{2}\s+£?([\d,]+\.\d{2})",
            # Standard formats
            r"(?:Grand\s+)?Total\s+(?:Amount|Due|Payable)?\s*:?\s*£?\s*([\d,]+\.\d{2})",
            r"Amount\s+Due\s*:?\s*£?\s*([\d,]+\.\d{2})",
            r"Balance\s+Due\s*:?\s*£?\s*([\d,]+\.\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self.amount_parser.parse_amount(match.group(1))
                if amount and amount > Decimal("0"):
                    return amount
        return Decimal("0")

    # Menkind HQ / billing address — never a store location
    _BILLING_CITIES = {"dorking"}

    # Canonical Menkind store names, sourced from the actual store data in the
    # Maintenance PO workbook — the union of the STORE columns across the data
    # sheets (CJL, ILUX, STORE MAINTENANCE, OTHER, ORDERS, APS, AURA AC) and the
    # CJL PIVOT / OTHER PIVOT row labels. This is the authoritative set the
    # extracted store must match — a candidate is only accepted when it snaps to
    # one of these, otherwise "" is returned ("if the app is not sure, no store
    # is shown"). Multi-word branch names and qualifiers (Bluewater Lower/Upper,
    # Meadowhall Upper, Glasgow Fort, Leeds White Rose) are first-class entries,
    # so qualifiers are preserved naturally.
    #
    # The extractor runs independently of Excel loading (it takes no workbook and
    # the live sheet may be open/locked), so the list is static. To add a store:
    # add its canonical name below. Old "<store> PB" rows in the workbook are
    # intentionally excluded, and obvious truncations/typos in the source data
    # ("Bluewater U", "Glasgow Silverbur", "Gatehead", "Livingstone") were
    # normalised to their correct names. Variant spellings that aren't canonical
    # (e.g. bare "Silverburn") are handled via _STORE_ALIASES, not listed here.
    # Display strings; matched case-insensitively.
    _KNOWN_STORES = [
        "Aberdeen", "Basingstoke", "Birmingham", "Blackpool", "Bluewater Lower",
        "Bluewater Upper", "Braehead", "Brighton", "Bristol", "Bromley",
        "Cambridge", "Cardiff", "Chelmsford", "Clarks Village", "Colchester",
        "Cribbs", "Cwmbran", "Derby", "Doncaster", "Dundee", "Eastbourne",
        "Edinburgh", "Edinburgh Fort", "Glasgow Buchanan", "Gateshead",
        "Glasgow Braehead", "Glasgow Fort", "Glasgow Silverburn",
        "Glasgow St Enoch", "Gloucester Quays", "Guildford", "Hanley",
        "Hereford", "High Wycombe", "Hull", "Lakeside", "Leeds White Rose",
        "Leicester", "Liverpool", "Livingston", "Maidstone", "Manchester",
        "Meadowhall", "Meadowhall Lower", "Meadowhall Upper", "Merry Hill",
        "Milton Keynes", "Newcastle", "Nottingham", "Oxford", "Peterborough",
        "Portsmouth", "Reading", "Redditch", "Southampton",
        "Staines", "Stratford", "Swansea", "Trafford", "Warrington", "Watford",
        "Worcester",
    ]

    # Variant spellings that appear in source data or on invoices but are not the
    # canonical store name. The matcher recognises the variant and returns the
    # canonical form, so e.g. an invoice or PO row saying just "Silverburn"
    # resolves to and displays as "Glasgow Silverburn". Keys are matched as
    # whole-store candidates (lower-cased); values must be in _KNOWN_STORES.
    _STORE_ALIASES = {
        "silverburn": "Glasgow Silverburn",
    }

    @staticmethod
    def _norm_words(s: str) -> list:
        """Lower-cased word tokens of a string (letters/apostrophes only)."""
        return re.findall(r"[a-z']+", s.lower())

    def _clean_town_or_empty(self, candidate: str) -> str:
        """Snap a raw candidate to a known store name, or return "".

        A candidate is only accepted when it matches one of ``_KNOWN_STORES`` —
        never a street, building, address blob, or company name. Steps:

        1. Strip postcodes and surrounding punctuation/whitespace.
        2. Exact (whole-string) match against a known store → return canonical.
        3. Otherwise find the longest known store name that appears as a
           contiguous run of words inside the candidate and snap to it. This
           recovers the real store from a noisy/merged line such as
           "Menkind Glasgow Fort Unit 4" → "Glasgow Fort", while a street blob
           like "31 Eden Centre Newlands Meadow High Wycombe" only matches its
           genuine store token if one is present.
        4. No known store found → "". "If the app is not sure, no store is shown."

        Longest-first matching means "Glasgow Fort" beats a bare "Glasgow" and
        "Bluewater Upper" beats "Bluewater".
        """
        if not candidate:
            return ""

        # Strip UK postcodes and tidy punctuation/whitespace.
        cleaned = re.sub(
            r"[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}", "", candidate, flags=re.IGNORECASE
        )
        cleaned = cleaned.strip(" \t,.-–—/").strip()
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return ""

        words = self._norm_words(cleaned)
        if not words:
            return ""

        # Matchable names as (canonical-display, word-tokens): the known stores
        # plus alias variants (which carry their canonical display). Longest
        # token-sequence first so the most specific branch (with qualifier) wins
        # over a bare town.
        matchable = [(s, self._norm_words(s)) for s in self._KNOWN_STORES]
        matchable += [
            (canonical, self._norm_words(alias))
            for alias, canonical in self._STORE_ALIASES.items()
        ]
        known = sorted(matchable, key=lambda kv: len(kv[1]), reverse=True)

        # 2. Exact whole-string match.
        for canonical, ktokens in known:
            if words == ktokens:
                return canonical

        # 3. Contiguous-subsequence match anywhere in the candidate.
        for canonical, ktokens in known:
            n = len(ktokens)
            for i in range(len(words) - n + 1):
                if words[i : i + n] == ktokens:
                    return canonical

        # 4. Not a known store → no store shown.
        return ""

    def _extract_store_location(self, text: str) -> str:
        """Extract the store name from invoice text using generic patterns.

        Returns a clean store name, or "" when no known store is found. The
        strategies below locate likely store text in priority order (the
        explicit "Menkind - <Store>" label first, boilerplate last); every
        candidate is passed through ``_clean_town_or_empty``, which only accepts
        it if it snaps to a real store in ``_KNOWN_STORES``. Street fragments,
        building names, address blobs, company words, and unknown towns are
        therefore rejected rather than shown as a store.
        """
        # 0. "Menkind - <Store>" — the explicit site label on Menkind invoices
        #    (e.g. ILUX "Menkind - Trafford", "Menkind - Milton Keynes"). The
        #    most reliable signal: capture to end of line / before an amount.
        #    Still validated, so a garbled merged label can't slip through.
        match = re.search(r"Menkind\s*-\s*([A-Za-z][A-Za-z'’ ]+?)\s*(?:£|\d|\n|$)", text)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 1. Explicit "Site Address" section — the store is usually the last
        #    line. pdfplumber merges multi-column layouts, so a line can be a
        #    street or a blob; store-set validation discards those.
        match = re.search(
            r"SITE\s+ADDRESS:\s*(.*?)(?:Site\s+Ref|Order\s+No|$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            lines = [
                line.strip()
                for line in match.group(1).strip().split("\n")
                if line.strip()
            ]
            # Try lines from the bottom up — the town is usually last, but a
            # street footer may sit below it; validation finds the real town.
            for line in reversed(lines):
                store = self._clean_town_or_empty(line)
                if store:
                    return store

        # 2. Explicit "Site Name" field — strip "Menkind" prefix if present
        match = re.search(
            r"Site\s+Name\s*:\s*(?:Menkind\s+)?(.+)", text, re.IGNORECASE
        )
        if match:
            store = self._clean_town_or_empty(match.group(1).split("\n")[0])
            if store:
                return store

        # 3. "X Shopping Centre" anywhere in text — extract X
        match = re.search(r"([A-Za-z][A-Za-z' ]+?)\s+Shopping\s+Centr", text, re.IGNORECASE)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 4. "Units XX-XX, Location" in description text (OCR may read l for 1)
        match = re.search(r"Units?\s+[\d\w]+-\d+\s*,\s*([A-Za-z' ]+)", text, re.IGNORECASE)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 5. "Reference <name> - <location>" field
        match = re.search(r"Reference\s+\w+\s*-\s*([A-Za-z' ]+)", text, re.IGNORECASE)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 6. City, Postcode pairs — pick first UNIQUE one that isn't the billing
        #    address. If a city appears multiple times it's likely the
        #    supplier's address, not the store. Each is store-validated.
        city_matches = re.findall(
            r"([A-Z][A-Za-z' ]{2,}?),\s*[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}", text
        )
        city_counts = {}
        for c in city_matches:
            key = c.strip().lower()
            city_counts[key] = city_counts.get(key, 0) + 1
        for c in city_matches:
            key = c.strip().lower()
            if key in self._BILLING_CITIES or city_counts[key] != 1:
                continue
            store = self._clean_town_or_empty(c)
            if store:
                return store

        # 7. "Menkind <StoreName>" — validate against known stores
        match = re.search(r"Menkind\s+([A-Za-z][A-Za-z' ]+)", text)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 8. Compco-style embedded reference
        match = re.search(r"##VAR37\s+(.+?)##", text)
        if match:
            store = self._clean_town_or_empty(match.group(1))
            if store:
                return store

        # 9. StringMatcher heuristic, validated against the known-store set.
        #
        # No whole-text scan beyond this: matching any known store name
        # anywhere in the document grabs the supplier's own HQ address (e.g.
        # Sunbelt Rentals' Warrington office in the footer) instead of the
        # delivery store. The targeted strategies above search the site/delivery
        # regions; if none yields a known store, return "" rather than guess.
        return self._clean_town_or_empty(
            self.string_matcher.extract_store_name(text) or ""
        )

    def _extract_description(self, text: str) -> str:
        """Extract work description."""
        patterns = [
            # "Description" or "Description:" followed by text
            r"Description\s*:\s*(.*?)(?:\n\n|Total|Visits|$)",
            r"Work\s+Description\s*:?\s*(.*?)(?:\n\n|Total|$)",
            r"Details\s*:?\s*(.*?)(?:\n\n|Total|$)",
            # Compco format
            r"Line\s+Item.*?Description.*?\n.*?\n\d+\s+(.+?)(?:\d+\.\d{2}|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                desc = re.sub(r"##\w+.*?##", "", desc)
                desc = " ".join(desc.split())
                if desc and len(desc) > 5:
                    return desc[:500]
        return ""

    def _identify_supplier(self, text: str, filename: str) -> str:
        """Identify supplier name from text or filename."""
        name, _ = _identify_supplier_registry(text, filename)
        return name

    def _identify_supplier_type(self, text: str, filename: str) -> str:
        """Identify supplier type code for sheet routing."""
        _, stype = _identify_supplier_registry(text, filename)
        return stype
