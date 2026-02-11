"""
Amount parsing utilities for handling currency values in invoices.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional
import re


class AmountParser:
    """Utility class for parsing currency amounts."""

    @staticmethod
    def parse_amount(amount_str: str) -> Optional[Decimal]:
        """
        Parse a currency amount string into a Decimal.

        Handles various formats:
        - "£116.50"
        - "116.50"
        - "1,234.56"
        - "£1,234.56"
        - "68.20\n" (with trailing whitespace/newline)

        Args:
            amount_str: The amount string to parse

        Returns:
            Decimal amount if parsing successful, None otherwise
        """
        if not amount_str:
            return None

        # Convert to string if not already
        amount_str = str(amount_str).strip()

        # Remove currency symbols and whitespace
        amount_str = amount_str.replace("£", "").replace("$", "").strip()

        # Remove commas (thousand separators)
        amount_str = amount_str.replace(",", "")

        # Try to extract amount using regex
        match = re.search(r"(\d+(?:\.\d{1,2})?)", amount_str)
        if match:
            try:
                return Decimal(match.group(1))
            except (InvalidOperation, ValueError):
                return None

        # Direct conversion attempt
        try:
            return Decimal(amount_str)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def parse_vat(
        total: Optional[Decimal], net: Optional[Decimal]
    ) -> Optional[Decimal]:
        """
        Calculate VAT from total and net amounts.

        Args:
            total: Total amount including VAT
            net: Net amount excluding VAT

        Returns:
            VAT amount (total - net), or None if inputs invalid
        """
        if total is None or net is None:
            return None

        try:
            return total - net
        except (TypeError, InvalidOperation):
            return None

    @staticmethod
    def calculate_total(
        net: Optional[Decimal], vat: Optional[Decimal]
    ) -> Optional[Decimal]:
        """
        Calculate total from net and VAT amounts.

        Args:
            net: Net amount excluding VAT
            vat: VAT amount

        Returns:
            Total amount (net + vat), or None if inputs invalid
        """
        if net is None or vat is None:
            return None

        try:
            return net + vat
        except (TypeError, InvalidOperation):
            return None
