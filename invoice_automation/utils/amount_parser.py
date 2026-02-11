"""
Amount parsing utilities for handling currency values in invoices.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional
import re


class AmountParser:
    """Utility class for parsing currency amounts."""

    # Pattern to match currency amounts with optional £ symbol
    AMOUNT_PATTERN = r"[£$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"

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
    def calculate_vat(
        net: Optional[Decimal], vat_rate: Decimal = Decimal("0.20")
    ) -> Optional[Decimal]:
        """
        Calculate VAT from net amount using a given rate.

        Args:
            net: Net amount excluding VAT
            vat_rate: VAT rate as decimal (default 0.20 for 20%)

        Returns:
            VAT amount, or None if net is None
        """
        if net is None:
            return None

        try:
            return net * vat_rate
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

    @staticmethod
    def is_valid_amount(
        amount: Optional[Decimal], min_value: Decimal = Decimal("0")
    ) -> bool:
        """
        Check if an amount is valid (non-negative by default).

        Args:
            amount: The amount to check
            min_value: Minimum valid amount (default 0)

        Returns:
            True if amount is valid, False otherwise
        """
        if amount is None:
            return False

        try:
            return amount >= min_value
        except (TypeError, InvalidOperation):
            return False

    @staticmethod
    def format_amount(amount: Optional[Decimal], currency_symbol: str = "£") -> str:
        """
        Format an amount as a currency string.

        Args:
            amount: The amount to format
            currency_symbol: Currency symbol to use (default £)

        Returns:
            Formatted currency string (e.g., "£116.50")
        """
        if amount is None:
            return f"{currency_symbol}0.00"

        return f"{currency_symbol}{amount:.2f}"

    @staticmethod
    def verify_vat_calculation(
        net: Optional[Decimal],
        vat: Optional[Decimal],
        total: Optional[Decimal],
        tolerance: Decimal = Decimal("0.02"),
    ) -> bool:
        """
        Verify that VAT calculation is correct: total = net + vat (within tolerance).

        Args:
            net: Net amount
            vat: VAT amount
            total: Total amount
            tolerance: Allowed difference (default 2p for rounding)

        Returns:
            True if calculation is valid, False otherwise
        """
        if None in (net, vat, total):
            return False

        try:
            calculated_total = net + vat
            difference = abs(calculated_total - total)
            return difference <= tolerance
        except (TypeError, InvalidOperation):
            return False
