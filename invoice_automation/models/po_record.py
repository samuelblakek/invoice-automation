"""
PO Record data model for representing Purchase Order records from Excel sheets.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class PORecord:
    """
    Represents a Purchase Order record from the Maintenance PO spreadsheet.

    Attributes:
        po_number: Purchase Order identifier
        sheet_name: Name of the Excel sheet where this PO is located
        row_index: Row index in the Excel sheet (for updates)
        store: Store location name
        originator: Person who originated the PO
        date: Date PO was created
        job_description: Description of the work/job
        quote_over_200: Quote reference if cost >£200
        authorized: Authorization status/person if cost >£200
        date_completed: Date work was completed
        invoice_no: Invoice number (to be filled)
        invoice_signed: Date invoice was signed (to be filled)
        invoice_amount: Invoice amount ex-VAT (to be filled)
        nominal_code: Cost/nominal code
        brand: Brand/store brand
        ticket_no: Ticket reference number
    """
    po_number: str
    sheet_name: str
    row_index: int
    store: str
    originator: Optional[str] = None
    date: Optional[datetime] = None
    job_description: Optional[str] = None
    quote_over_200: Optional[str] = None
    authorized: Optional[str] = None
    date_completed: Optional[datetime] = None
    invoice_no: Optional[str] = None
    invoice_signed: Optional[datetime] = None
    invoice_amount: Optional[Decimal] = None
    nominal_code: Optional[str] = None
    brand: Optional[str] = None
    ticket_no: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"PORecord(po_number='{self.po_number}', "
            f"sheet='{self.sheet_name}', "
            f"store='{self.store}', "
            f"invoice_no='{self.invoice_no}')"
        )

    def is_invoiced(self) -> bool:
        """Check if this PO already has an invoice number."""
        return bool(self.invoice_no and str(self.invoice_no).strip())

    def has_quote_authorization(self) -> bool:
        """Check if quote is authorized (both quote ref and authorization present)."""
        has_quote = bool(self.quote_over_200 and str(self.quote_over_200).strip())
        has_auth = bool(self.authorized and str(self.authorized).strip())
        return has_quote and has_auth

    def needs_quote_authorization(self) -> bool:
        """Check if this PO has a quote reference (indicating >£200 cost)."""
        return bool(self.quote_over_200 and str(self.quote_over_200).strip())
