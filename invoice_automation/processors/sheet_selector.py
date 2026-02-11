"""
Sheet selector for mapping suppliers to Excel sheets.
"""

from typing import Optional


class SheetSelector:
    """Utility for selecting the correct Excel sheet based on supplier."""

    # Mapping of supplier types to sheet names
    SUPPLIER_SHEET_MAP = {
        "AAW": "AAW NATIONAL (PANDA)",
        "CJL": "CJL",
        "APS": "APS",
        "AMAZON": "ORDERS",
        "COMPCO": "OTHER",
        "AURA": "AURA AC",
        "STORE_MAINTENANCE": "STORE MAINTENANCE",
        "OTHER": "OTHER",
        "GENERIC": "OTHER",
        # New suppliers
        "SUNBELT": "OTHER",
        "MAXWELL_JONES": "OTHER",
        "METRO_SECURITY": "OTHER",
        "ILUX": "OTHER",
        "LAMPSHOP": "ORDERS",
    }

    @staticmethod
    def get_sheet_name(supplier_type: str) -> Optional[str]:
        """
        Get the sheet name for a given supplier type.

        Args:
            supplier_type: Supplier type (e.g., 'AAW', 'CJL')

        Returns:
            Sheet name, or None if not mapped
        """
        return SheetSelector.SUPPLIER_SHEET_MAP.get(supplier_type.upper())

    @staticmethod
    def get_all_sheets() -> list:
        """
        Get list of all maintenance PO sheets.

        Returns:
            List of unique sheet names
        """
        return list(set(SheetSelector.SUPPLIER_SHEET_MAP.values()))
