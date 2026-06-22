"""Tests for the model invariants added in the type refactor.

Run directly (no pytest needed):
    .venv/Scripts/python.exe -m tests.test_models
"""

from datetime import datetime
from decimal import Decimal

from invoice_automation.models import (
    Invoice,
    ValidationResult,
    Validation,
    ValidationSeverity,
)


def _inv(**overrides) -> Invoice:
    kw = dict(
        invoice_number="INV-1",
        invoice_date=datetime(2026, 4, 1),
        supplier_name="iLux",
        supplier_type="GENERIC",
        po_number="",
        store_location="",
        store_address="",
        net_amount=Decimal("100.00"),
        vat_amount=Decimal("20.00"),
        total_amount=Decimal("120.00"),
        nominal_code="",
        description="",
        raw_text="",
        pdf_path="x.pdf",
    )
    kw.update(overrides)
    return Invoice(**kw)


def test_invoice_requires_invoice_number():
    raised = False
    try:
        _inv(invoice_number="   ")
    except ValueError:
        raised = True
    assert raised, "Invoice with blank invoice_number should raise ValueError"


def test_invoice_coerces_amounts_to_decimal():
    inv = _inv(net_amount=100, vat_amount=20.0, total_amount="120")
    assert isinstance(inv.net_amount, Decimal)
    assert isinstance(inv.vat_amount, Decimal)
    assert isinstance(inv.total_amount, Decimal)


def test_has_po_and_has_store_ignore_whitespace():
    assert _inv(po_number=" OT1 ").has_po
    assert not _inv(po_number="   ").has_po
    assert _inv(store_location="Trafford").has_store
    assert not _inv(store_location="").has_store


def test_validationresult_errors_warnings_are_derived():
    r = ValidationResult(invoice=None, po_record=None)
    r.add_validation(
        Validation("c1", False, None, None, ValidationSeverity.ERROR, "boom")
    )
    r.add_validation(
        Validation("c2", False, None, None, ValidationSeverity.WARNING, "careful")
    )
    r.add_validation(
        Validation("c3", True, None, None, ValidationSeverity.INFO, "ok")
    )
    assert r.errors == ["boom"]
    assert r.warnings == ["careful"]
    assert r.is_valid is False
    assert r.can_auto_update is False  # no PO record


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
