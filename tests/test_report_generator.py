"""Regression test for report file encoding.

The detailed report writes a "✓" pass symbol (and "£" amounts). The file was
opened without an explicit encoding, so on Windows (cp1252 default) writing the
"✓" raised UnicodeEncodeError and crashed processing. Reports must be written as
UTF-8.

Run directly (no pytest needed):
    .venv/Scripts/python.exe -m tests.test_report_generator
"""

import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from invoice_automation.models import (
    Invoice,
    ValidationResult,
    Validation,
    ValidationSeverity,
)
from invoice_automation.reports.report_generator import ReportGenerator


def _result() -> ValidationResult:
    inv = Invoice(
        invoice_number="INV-1",
        invoice_date=datetime(2026, 4, 1),
        supplier_name="ILUX Lighting",
        supplier_type="GENERIC",
        po_number="OT0348",
        store_location="Southampton",
        store_address="",
        net_amount=Decimal("820.00"),
        vat_amount=Decimal("164.00"),
        total_amount=Decimal("984.00"),
        nominal_code="7820",
        description="",
        raw_text="",
        pdf_path="SI-3276.pdf",
    )
    r = ValidationResult(invoice=inv, po_record=None, pdf_path="SI-3276.pdf")
    # A passed validation writes the "✓" symbol; the £ amount is written too.
    r.add_validation(
        Validation("PO Match", True, None, None, ValidationSeverity.INFO, "matched")
    )
    return r


def test_detailed_report_writes_utf8_symbols():
    rg = ReportGenerator([_result()])
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "report.txt"
        rg.save_detailed_report(path)  # must not raise UnicodeEncodeError
        text = path.read_text(encoding="utf-8")
    assert "✓" in text, "detailed report should contain the ✓ pass symbol"
    assert "£" in text, "detailed report should contain the £ amount"


def test_summary_csv_writes_without_error():
    rg = ReportGenerator([_result()])
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "summary.csv"
        rg.save_summary_csv(path)  # must not raise
        text = path.read_text(encoding="utf-8")
    assert "INV-1" in text


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
            except Exception as exc:
                failures += 1
                print(f"ERROR {_name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
