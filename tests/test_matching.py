"""Regression tests for PO matching and amount validation.

Builds a small .xlsx fixture (header below several title rows, like the real
Maintenance PO workbook) and exercises the money-path logic that previously had
no automated coverage: exact-PO matching, the cross-sheet fallback, the
"stated PO not found" guard, exact-vs-substring PO matching, fuzzy-only-for-
PO-less invoices, and net+VAT==total amount reconciliation.

Run directly (no pytest needed):
    .venv/Scripts/python.exe -m tests.test_matching
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import openpyxl

from invoice_automation.models import Invoice
from invoice_automation.processors import ExcelReader
from invoice_automation.validators import InvoiceValidator
from invoice_automation.validators.po_matcher import POMatcher


def _make_workbook(path: Path) -> None:
    wb = openpyxl.Workbook()
    other = wb.active
    other.title = "OTHER"
    for _ in range(4):  # title/legend rows before the header (header at row 5)
        other.append(["Maintenance title"])
    other.append(
        ["PO", "ORIGINATOR", "DATE", "STORE", "BRAND", "TICKET NO.",
         "COMPANY NAME", "JOB DESCRIPTION", "QUOTE OVER £200", "AUTHORISED",
         "INVOICE NO.", "INVOICE AMOUNT (EX VAT)"]
    )
    other.append(["OT0402", "SB", "2026-04-01", "Trafford", "Menkind", "123118",
                  "iLux", "Loose beam", "", "", "", ""])
    other.append(["OT0403", "SB", "2026-04-01", "Aberdeen", "Menkind", "122938",
                  "Brodex", "Water RA", "", "", "81355", ""])

    ilux = wb.create_sheet("ILUX")
    for _ in range(5):  # ILUX header sits one row lower than OTHER
        ilux.append(["Maintenance title"])
    ilux.append(["PO", "ORIGINATOR", "DATE", "STORE", "BRAND", "TICKET NO.",
                 "JOB DESCRIPTION"])
    ilux.append(["LUX004", "SB", "2026-04-14", "Chelmsford", "Menkind", "123352",
                 "Blocked toilet"])
    wb.save(path)


def _reader() -> ExcelReader:
    path = Path(tempfile.mkdtemp()) / "wb.xlsx"
    _make_workbook(path)
    return ExcelReader(path)


def _inv(po="", store="", supplier="iLux", supplier_type="GENERIC",
         net="100.00", vat="20.00", total="120.00") -> Invoice:
    return Invoice(
        invoice_number="INV-TEST",
        invoice_date=datetime(2026, 4, 1),
        supplier_name=supplier,
        supplier_type=supplier_type,
        po_number=po,
        store_location=store,
        store_address="",
        net_amount=Decimal(net),
        vat_amount=Decimal(vat),
        total_amount=Decimal(total),
        nominal_code="",
        description="",
        raw_text="",
        pdf_path="test.pdf",
    )


def test_exact_po_match_in_mapped_sheet():
    rec, _ = POMatcher(_reader()).find_po_record(_inv(po="OT0402", store="Trafford"))
    assert rec is not None and rec.po_number == "OT0402" and rec.sheet_name == "OTHER"


def test_cross_sheet_po_fallback():
    # ILUX maps to OTHER, but LUX004 lives on the ILUX sheet — cross-sheet finds it.
    rec, _ = POMatcher(_reader()).find_po_record(
        _inv(po="LUX004", store="Chelmsford", supplier_type="ILUX")
    )
    assert rec is not None and rec.po_number == "LUX004" and rec.sheet_name == "ILUX"


def test_stated_po_not_found_returns_none():
    rec, vals = POMatcher(_reader()).find_po_record(
        _inv(po="ZZ9999", store="Trafford")
    )
    assert rec is None
    assert any("not found" in v.message.lower() for v in vals)


def test_substring_po_does_not_match_longer_po():
    # "OT040" must NOT match "OT0402" (exact-token, not substring).
    rec, _ = POMatcher(_reader()).find_po_record(_inv(po="OT040", store="Trafford"))
    assert rec is None


def test_poless_invoice_fuzzy_goes_to_review_not_auto():
    # No PO on the invoice: fuzzy store/supplier/amount scoring still finds a
    # candidate, but it is a GUESS — it must never auto-update. It lands in
    # Needs Review with clear messaging so a human confirms the PO.
    result = InvoiceValidator(_reader()).validate(_inv(po="", store="Trafford"))
    assert result.po_record is not None and result.po_record.po_number == "OT0402"
    assert not result.can_auto_update
    assert result.needs_review
    assert any("NEEDS REVIEW" in e for e in result.errors)


def test_amount_reconciliation_blocks_auto_update():
    validator = InvoiceValidator(_reader())
    # net + VAT != total -> reviewable, not auto-updated.
    bad = validator.validate(
        _inv(po="OT0402", store="Trafford", net="100.00", vat="20.00", total="200.00")
    )
    assert not bad.can_auto_update and bad.needs_review


def test_reconciling_amounts_auto_update():
    validator = InvoiceValidator(_reader())
    good = validator.validate(
        _inv(po="OT0402", store="Trafford", net="100.00", vat="20.00", total="120.00")
    )
    assert good.can_auto_update


if __name__ == "__main__":
    import sys

    failures = 0
    for _name, _fn in sorted(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {_name}: {exc}")
            except Exception as exc:  # surface fixture/wiring errors too
                failures += 1
                print(f"ERROR {_name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
