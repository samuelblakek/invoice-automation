"""
String matching utilities for fuzzy matching and pattern extraction.
"""

from typing import Optional
import re
from fuzzywuzzy import fuzz


class StringMatcher:
    """Utility class for string matching and extraction."""

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
