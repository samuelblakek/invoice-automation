"""
Date parsing utilities for handling various date formats in invoices.
"""
from datetime import datetime
from typing import Optional
import re
from dateutil import parser as dateutil_parser


class DateParser:
    """Utility class for parsing dates in various formats."""

    # Common date patterns found in invoices
    DATE_PATTERNS = [
        # DD Month YYYY (e.g., "08 May 2025", "3 April 2025")
        (r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', '%d %B %Y'),
        (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', '%d %b %Y'),

        # DD/MM/YYYY or DD-MM-YYYY
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', None),  # Will use dateutil

        # DD.MM.YY (e.g., "07.05.25")
        (r'(\d{1,2})\.(\d{1,2})\.(\d{2})', '%d.%m.%y'),

        # YYYY-MM-DD (ISO format)
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
    ]

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.

        Handles various date formats commonly found in invoices:
        - "08 May 2025"
        - "3 April 2025"
        - "12/03/2025"
        - "07.05.25"
        - "2025-03-15"

        Args:
            date_str: The date string to parse

        Returns:
            datetime object if parsing successful, None otherwise
        """
        if not date_str or not isinstance(date_str, str):
            return None

        # Clean the string
        date_str = date_str.strip()

        # Try each pattern
        for pattern, date_format in DateParser.DATE_PATTERNS:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if date_format:
                        # Use strptime with specific format
                        return datetime.strptime(match.group(0), date_format)
                    else:
                        # Use dateutil parser for flexible parsing
                        return dateutil_parser.parse(match.group(0), dayfirst=True)
                except (ValueError, TypeError):
                    continue

        # Fallback: try dateutil parser directly
        try:
            return dateutil_parser.parse(date_str, dayfirst=True)
        except (ValueError, TypeError, dateutil_parser.ParserError):
            return None

    @staticmethod
    def format_date(date: Optional[datetime], format_str: str = '%Y-%m-%d') -> str:
        """
        Format a datetime object as a string.

        Args:
            date: The datetime object to format
            format_str: The format string (default: ISO date)

        Returns:
            Formatted date string, or empty string if date is None
        """
        if date is None:
            return ""
        return date.strftime(format_str)

    @staticmethod
    def get_today() -> datetime:
        """Get today's date."""
        return datetime.now()

    @staticmethod
    def is_valid_date(date: Optional[datetime], min_year: int = 2020, max_year: int = 2030) -> bool:
        """
        Check if a date is valid (within reasonable range).

        Args:
            date: The date to check
            min_year: Minimum valid year
            max_year: Maximum valid year

        Returns:
            True if date is valid, False otherwise
        """
        if date is None:
            return False
        return min_year <= date.year <= max_year
