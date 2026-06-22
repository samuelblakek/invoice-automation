"""Regression tests for GenericExtractor invoice-number extraction.

Focuses on the filename fallback used when no in-PDF invoice-number pattern
matches. The hyphenated "INV-NNNNN" naming convention previously yielded no
invoice number, raising "Could not extract invoice number from <file>".

Run directly (no pytest needed):
    .venv/Scripts/python.exe -m tests.test_generic_extractor
or under pytest if/when it is added.
"""

from invoice_automation.extractors.generic_extractor import GenericExtractor


def _inv_num(filename: str, text: str = "") -> str:
    return GenericExtractor()._extract_invoice_number(text, filename)


def test_hyphenated_inv_filename_fallback():
    # Content carries no recognisable invoice-number field; filename holds it.
    assert _inv_num("INV-10801.pdf") == "INV-10801"
    assert _inv_num("INV-11027.pdf") == "INV-11027"


def test_plain_inv_filename_still_works():
    assert _inv_num("INV29453.pdf") == "INV29453"


def test_underscore_and_space_separators():
    assert _inv_num("INV_10801.pdf") == "INV_10801"
    assert _inv_num("INV 10801.pdf") == "INV10801"


def test_psi_filename_fallback():
    assert _inv_num("PSI577608.pdf") == "577608"


def test_content_pattern_takes_priority_over_filename():
    # An in-PDF invoice number must win over the filename fallback.
    assert _inv_num("INV-99999.pdf", "Invoice Number: SI-3276") == "SI-3276"


def _vat(text: str) -> str:
    return str(GenericExtractor()._extract_vat_amount(text))


def test_vat_total_tax_line():
    # ILUX current template: "Total Tax" is the VAT, "Total ex VAT" is the net.
    text = "Bank details Total ex VAT £115.00\nTotal Tax £23.00\nTotal £138.00"
    assert _vat(text) == "23.00"


def test_vat_does_not_match_ex_vat_net_line():
    # The net line must never be read as VAT, even with no explicit VAT line.
    text = "Total ex VAT £115.00\nTotal £138.00"
    assert _vat(text) != "115.00"


def _total(text: str) -> str:
    return str(GenericExtractor()._extract_total_amount(text))


def test_total_with_corrupted_pound_glyph():
    # Some fonts render "£" as "f.". The invoice total must still win over the
    # sub total, not be skipped (which previously left SUB TOTAL as the total).
    text = "SUB TOTAL 1010.00\nVAT 202.00\nINVOICE TOTAL f.1212.00"
    assert _total(text) == "1212.00"


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
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
