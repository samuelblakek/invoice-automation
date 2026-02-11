"""
String matching utilities for fuzzy matching and pattern extraction.
"""

from typing import Optional, Tuple, List
import re
from fuzzywuzzy import fuzz


class StringMatcher:
    """Utility class for string matching and extraction."""

    # PO number patterns for different suppliers
    PO_PATTERNS = {
        "AAW": r"PS\d{10,12}",
        "CJL": r"CJL\d{3}",
        "AMAZON": r"ORD\d{3,4}",
        "COMPCO": r"ER\d{2}/\d{5}",
        "APS": r"[A-Z]{2}\d{2}/\d{5}",  # Generic pattern
        "GENERIC": r"[A-Z]{2,4}\d{3,6}",  # Fallback pattern
    }

    @staticmethod
    def fuzzy_match(s1: str, s2: str, threshold: int = 80) -> bool:
        """
        Check if two strings match using fuzzy matching.

        Args:
            s1: First string
            s2: Second string
            threshold: Minimum similarity score (0-100) to consider a match

        Returns:
            True if strings match above threshold, False otherwise
        """
        if not s1 or not s2:
            return False

        # Normalize strings
        s1_norm = StringMatcher.normalize_string(s1)
        s2_norm = StringMatcher.normalize_string(s2)

        # Calculate similarity score
        score = fuzz.token_sort_ratio(s1_norm, s2_norm)

        return score >= threshold

    @staticmethod
    def fuzzy_match_score(s1: str, s2: str) -> int:
        """
        Get the fuzzy match score between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0-100)
        """
        if not s1 or not s2:
            return 0

        # Normalize strings
        s1_norm = StringMatcher.normalize_string(s1)
        s2_norm = StringMatcher.normalize_string(s2)

        # Calculate similarity score
        return fuzz.token_sort_ratio(s1_norm, s2_norm)

    @staticmethod
    def normalize_string(s: str) -> str:
        """
        Normalize a string for comparison.

        Converts to lowercase, removes extra whitespace and punctuation.

        Args:
            s: The string to normalize

        Returns:
            Normalized string
        """
        if not s:
            return ""

        # Convert to lowercase
        s = s.lower()

        # Remove common punctuation
        s = re.sub(r"[,.\-_/\\]", " ", s)

        # Remove extra whitespace
        s = " ".join(s.split())

        return s

    @staticmethod
    def extract_po_number(
        text: str, supplier_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract PO number from text using pattern matching.

        Args:
            text: The text to search
            supplier_type: Optional supplier type to use specific pattern

        Returns:
            Extracted PO number, or None if not found
        """
        if not text:
            return None

        # Try supplier-specific pattern first
        if supplier_type and supplier_type.upper() in StringMatcher.PO_PATTERNS:
            pattern = StringMatcher.PO_PATTERNS[supplier_type.upper()]
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        # Try all patterns
        for pattern in StringMatcher.PO_PATTERNS.values():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    @staticmethod
    def extract_store_name(address: str) -> Optional[str]:
        """
        Extract store name from an address string.

        Common patterns:
        - "Menkind Limited - Maidstone - Address"
        - "Site: Maidstone"
        - "Maidstone Store"

        Args:
            address: The address string

        Returns:
            Extracted store name, or None if not found
        """
        if not address:
            return None

        # Pattern 1: "Menkind Limited - StoreName - ..."
        match = re.search(r"Menkind Limited\s*-\s*([^-\n]+)", address, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 2: "Site: StoreName"
        match = re.search(r"Site:\s*([^\n]+)", address, re.IGNORECASE)
        if match:
            store_part = match.group(1).strip()
            # Remove trailing address parts
            if "-" in store_part:
                return store_part.split("-")[0].strip()
            return store_part

        # Pattern 3: Look for common UK location names
        # Extract first line or first significant part
        lines = address.split("\n")
        if lines:
            first_line = lines[0].strip()
            # Remove company name if present
            first_line = re.sub(r"Menkind Limited", "", first_line, flags=re.IGNORECASE)
            first_line = first_line.strip("-,. ")
            if first_line:
                return first_line

        return None

    @staticmethod
    def find_best_match(
        query: str, choices: List[str], threshold: int = 70
    ) -> Tuple[Optional[str], int]:
        """
        Find the best matching string from a list of choices.

        Args:
            query: The string to match
            choices: List of strings to match against
            threshold: Minimum score to consider valid

        Returns:
            Tuple of (best_match, score), or (None, 0) if no match above threshold
        """
        if not query or not choices:
            return None, 0

        best_match = None
        best_score = 0

        query_norm = StringMatcher.normalize_string(query)

        for choice in choices:
            if not choice:
                continue

            choice_norm = StringMatcher.normalize_string(choice)
            score = fuzz.token_sort_ratio(query_norm, choice_norm)

            if score > best_score:
                best_score = score
                best_match = choice

        if best_score >= threshold:
            return best_match, best_score

        return None, 0

    @staticmethod
    def extract_nominal_code(text: str) -> Optional[str]:
        """
        Extract nominal code from text.

        Nominal codes are typically 4 digits (e.g., 7820, 7800, 7530).

        Args:
            text: The text to search

        Returns:
            Extracted nominal code, or None if not found
        """
        if not text:
            return None

        # Look for 4-digit nominal codes
        match = re.search(r"\b(7\d{3})\b", text)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def clean_invoice_number(invoice_num: str) -> str:
        """
        Clean and normalize invoice number.

        Args:
            invoice_num: Raw invoice number

        Returns:
            Cleaned invoice number
        """
        if not invoice_num:
            return ""

        # Remove whitespace and common prefixes
        invoice_num = invoice_num.strip()
        invoice_num = re.sub(
            r"^(invoice|inv|#)\s*", "", invoice_num, flags=re.IGNORECASE
        )

        return invoice_num
