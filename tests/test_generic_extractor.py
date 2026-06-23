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


def _store(text: str) -> str:
    return GenericExtractor()._extract_store_location(text)


def _po(text: str) -> str:
    return GenericExtractor()._extract_po_number(text)


def test_menkind_dash_store_single_word():
    text = "Site Address:\nMenkind - Trafford\nUnit L78, Trafford Centre"
    assert _store(text) == "Trafford"


def test_menkind_dash_store_multi_word():
    # Genuine multi-word store names must not be truncated.
    assert _store("Menkind - Milton Keynes\nUnit 4") == "Milton Keynes"
    assert _store("Menkind - Leeds White Rose\nUnit 4") == "Leeds White Rose"


def test_store_qualifier_preserved():
    # Lower/Upper/Fort are real parts of a branch name (per the Maintenance PO
    # workbook) and must be preserved, not stripped to the bare town.
    assert _store("Menkind - Bluewater Lower\nUnit 4") == "Bluewater Lower"
    assert _store("Menkind - Meadowhall Lower\nUnit 4") == "Meadowhall Lower"
    assert _store("Menkind - Meadowhall Upper\nUnit 4") == "Meadowhall Upper"
    assert _store("Site Name : Menkind Glasgow Fort Unit 22") == "Glasgow Fort"


def test_store_snaps_to_bare_store_when_branch_unknown():
    # A qualifier that is not a real branch snaps to the bare store rather than
    # inventing one. "Cardiff Upper" is not a real branch; bare "Cardiff" is a
    # real store.
    assert _store("Menkind - Cardiff Upper\nUnit 4") == "Cardiff"


def test_store_alias_resolves_to_canonical():
    # A variant spelling resolves to the canonical store name: bare "Silverburn"
    # displays as "Glasgow Silverburn".
    assert _store("Menkind - Silverburn\nUnit 4") == "Glasgow Silverburn"
    assert _store("Menkind - Glasgow Silverburn\nUnit 4") == "Glasgow Silverburn"


def test_store_not_taken_from_footer():
    # The footer registration line must never be returned as the store.
    text = "Menkind - Derby\nRegistered in England No: 14072087 VAT Reg No: 475706660"
    assert _store(text) == "Derby"


def test_store_known_store_from_site_address():
    # A real store on its own line is returned; the street line above is not.
    text = "SITE ADDRESS:\nUnit 12 Kings Inch Road\nBraehead PA4 8XQ\nSite Ref 99"
    assert _store(text) == "Braehead"


def test_store_street_fragment_rejected():
    # "Kings Inch Road" is a street, not a store — must not be returned. The
    # known store on the unit line (Braehead) is returned instead.
    text = "SITE ADDRESS:\nMenkind Braehead\nKings Inch Road\nSite Ref 99"
    store = _store(text)
    assert "Road" not in store
    assert store == "Braehead"


def test_store_unknown_town_returns_empty():
    # A town that is not a Menkind store must yield "" — "if not sure, no
    # store is shown". Taunton appears on some invoices but is not a store.
    assert _store("SITE ADDRESS:\nSome Street\nTaunton TA1 1AA\nSite Ref 5") == ""


def test_store_address_blob_returns_empty():
    # A merged-column address blob with no known store token must return "" —
    # the app shows no store rather than a street fragment.
    text = "SITE ADDRESS:\n31 Eden Centre Newlands Meadow Faketon\nOrder No 5"
    assert _store(text) == ""


def test_store_skips_billing_company_line():
    # The billing line "Menkind Ltd, RH4 1AA" must not yield "Ltd"; the real
    # delivery store (Reading) wins.
    text = "Invoice to Menkind Ltd, RH4 1AA\nDelivery 12 Long Lane, Reading, RG1 2AB"
    assert _store(text) == "Reading"


def test_store_menkind_dash_validated_store():
    # The trusted Menkind - <Store> label yields clean store names, including
    # multi-word ones.
    assert _store("Menkind - Trafford\nUnit L78") == "Trafford"
    assert _store("Menkind - High Wycombe\nUnit 4") == "High Wycombe"


def test_store_bare_glasgow_is_not_a_store():
    # Bare "Glasgow" is not a store (only the specific Glasgow branches are),
    # so it must return "" rather than guessing.
    assert _store("Menkind - Glasgow\nUnit 4") == ""


def test_po_order_number_strips_ticket_prefix():
    # "<ticket>/<PO>" — the PO is the part after the slash.
    assert _po("Order number 123118/OT0402") == "OT0402"
    assert _po("Order number 123352/LUX004") == "LUX004"


def test_po_order_number_without_prefix():
    assert _po("Order number LUX010") == "LUX010"


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
