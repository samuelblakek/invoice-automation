"""
Base extractor class for PDF invoice extraction.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict
import re
import pdfplumber
from functools import lru_cache

from ..models import Invoice
from ..utils import DateParser, AmountParser, StringMatcher


class PDFExtractionError(Exception):
    """Exception raised when PDF extraction fails."""
    pass


class BaseExtractor(ABC):
    """
    Abstract base class for invoice extractors.

    Each supplier-specific extractor should inherit from this class
    and implement the extract() method.
    """

    # Class-level cache for compiled regex patterns
    _pattern_cache: Dict[tuple, re.Pattern] = {}

    def __init__(self):
        self.date_parser = DateParser()
        self.amount_parser = AmountParser()
        self.string_matcher = StringMatcher()

    @classmethod
    def _get_compiled_pattern(cls, pattern: str, flags: int = 0) -> re.Pattern:
        """
        Get a compiled regex pattern from cache, or compile and cache it.

        Args:
            pattern: Regex pattern string
            flags: Regex flags

        Returns:
            Compiled regex pattern
        """
        cache_key = (pattern, flags)
        if cache_key not in cls._pattern_cache:
            cls._pattern_cache[cache_key] = re.compile(pattern, flags)
        return cls._pattern_cache[cache_key]

    @abstractmethod
    def extract(self, pdf_path: Path) -> Invoice:
        """
        Extract invoice data from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Invoice object with extracted data

        Raises:
            PDFExtractionError: If extraction fails
        """
        pass

    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as a single string

        Raises:
            PDFExtractionError: If PDF cannot be read
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return '\n'.join(text_parts)
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract text from {pdf_path}: {str(e)}")

    def _extract_first_page_text(self, pdf_path: Path) -> str:
        """
        Extract text from the first page only.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text from first page

        Raises:
            PDFExtractionError: If PDF cannot be read
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    return pdf.pages[0].extract_text() or ""
                return ""
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract first page from {pdf_path}: {str(e)}")

    def _find_pattern(self, text: str, pattern: str, flags: int = 0) -> Optional[str]:
        """
        Find a regex pattern in text using cached compiled patterns.

        Args:
            text: Text to search
            pattern: Regex pattern
            flags: Regex flags (default 0)

        Returns:
            Matched string, or None if not found
        """
        compiled = self._get_compiled_pattern(pattern, flags)
        match = compiled.search(text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return None

    def _find_all_patterns(self, text: str, pattern: str, flags: int = 0) -> list:
        """
        Find all occurrences of a regex pattern in text using cached compiled patterns.

        Args:
            text: Text to search
            pattern: Regex pattern
            flags: Regex flags (default 0)

        Returns:
            List of matched strings
        """
        compiled = self._get_compiled_pattern(pattern, flags)
        matches = compiled.findall(text)
        return matches if matches else []

    def _extract_field_value(self, text: str, field_name: str, pattern: Optional[str] = None) -> Optional[str]:
        """
        Extract a field value that follows a field name/label.

        Example: "Invoice No: 12345" -> "12345"

        Args:
            text: Text to search
            field_name: Name/label of the field
            pattern: Optional regex pattern for the value (default: captures until newline)

        Returns:
            Extracted value, or None if not found
        """
        if pattern is None:
            pattern = r'([^\n]+)'

        # Build regex pattern: field_name followed by optional separator and value
        full_pattern = rf'{re.escape(field_name)}\s*[:=]?\s*{pattern}'

        compiled = self._get_compiled_pattern(full_pattern, re.IGNORECASE)
        match = compiled.search(text)
        if match:
            return match.group(1).strip()
        return None

    def _clean_text(self, text: Optional[str]) -> str:
        """
        Clean extracted text (remove extra whitespace, newlines, etc.).

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        return text.strip()

    def _validate_required_fields(self, invoice: Invoice) -> None:
        """
        Validate that required fields are present in the invoice.

        Args:
            invoice: Invoice object to validate

        Raises:
            PDFExtractionError: If required fields are missing
        """
        required_fields = {
            'invoice_number': invoice.invoice_number,
            'net_amount': invoice.net_amount,
        }

        missing_fields = [
            field_name for field_name, value in required_fields.items()
            if not value or (isinstance(value, str) and not value.strip())
        ]

        if missing_fields:
            raise PDFExtractionError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
