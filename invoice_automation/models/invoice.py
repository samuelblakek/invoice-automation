"""
Invoice data model for representing extracted PDF invoice data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any


@dataclass
class Invoice:
    """
    Represents an invoice extracted from a PDF file.

    Attributes:
        invoice_number: Unique invoice identifier
        invoice_date: Date invoice was issued
        supplier_name: Name of the supplier/vendor
        supplier_type: Type/category of supplier (AAW, CJL, APS, etc.)
        po_number: Purchase Order reference number
        store_location: Store name/location
        store_address: Full store address from invoice
        net_amount: Amount excluding VAT
        vat_amount: VAT amount
        total_amount: Total including VAT
        nominal_code: Cost/nominal code (optional)
        description: Description of work/goods
        raw_text: Full extracted text from PDF
        pdf_path: Path to the source PDF file
        extracted_fields: Dictionary of all extracted fields
    """

    invoice_number: str
    invoice_date: Optional[datetime]
    supplier_name: str
    supplier_type: str
    po_number: str
    store_location: str
    store_address: str
    net_amount: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    nominal_code: Optional[str]
    description: str
    raw_text: str
    pdf_path: str
    extracted_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # An invoice with no number is meaningless — make it unrepresentable
        # rather than relying on each extractor to check.
        if not self.invoice_number or not str(self.invoice_number).strip():
            raise ValueError("Invoice.invoice_number must be a non-empty string")
        # Lock the "money is Decimal" invariant at the boundary so a stray
        # float/str/int from a caller can't break amount comparisons downstream.
        for name in ("net_amount", "vat_amount", "total_amount"):
            value = getattr(self, name)
            if not isinstance(value, Decimal):
                setattr(self, name, Decimal(str(value)))

    @property
    def has_po(self) -> bool:
        """True when the invoice carries a usable (non-blank) PO number."""
        return bool(self.po_number and str(self.po_number).strip())

    @property
    def has_store(self) -> bool:
        """True when the invoice carries a usable (non-blank) store location."""
        return bool(self.store_location and str(self.store_location).strip())

    def __repr__(self) -> str:
        return (
            f"Invoice(invoice_number='{self.invoice_number}', "
            f"supplier='{self.supplier_name}', "
            f"po_number='{self.po_number}', "
            f"net_amount={self.net_amount})"
        )
