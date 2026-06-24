"""Tests for the editable store registry (data/known_stores.json backing).

Run directly (no pytest needed):
    .venv/Scripts/python.exe -m tests.test_store_registry
"""

import json
import tempfile
from contextlib import contextmanager
from pathlib import Path

from invoice_automation.utils import store_registry as sr


@contextmanager
def _temp_store_path(write: dict | None = None):
    """Redirect store_registry.STORE_DATA_PATH at a throwaway file so tests never
    touch the real data/known_stores.json. Optionally seed it with `write`."""
    original = sr.STORE_DATA_PATH
    tmpdir = Path(tempfile.mkdtemp())
    path = tmpdir / "known_stores.json"
    if write is not None:
        path.write_text(json.dumps(write), encoding="utf-8")
    sr.STORE_DATA_PATH = path
    try:
        yield path
    finally:
        sr.STORE_DATA_PATH = original


def test_load_stores_seeded_list_has_known_stores():
    # The committed data/known_stores.json (or the defaults) must include real stores.
    stores = sr.load_stores()
    assert len(stores) >= 60
    for name in ("Trafford", "Glasgow Fort", "Milton Keynes"):
        assert name in stores, f"{name} missing from store list"


def test_load_falls_back_to_defaults_when_file_missing():
    with _temp_store_path():  # no file written
        assert sr.load_stores() == list(sr.DEFAULT_STORES)


def test_load_falls_back_to_defaults_when_file_corrupt():
    with _temp_store_path() as path:
        path.write_text("{ not valid json", encoding="utf-8")
        assert sr.load_stores() == list(sr.DEFAULT_STORES)


def test_save_and_load_roundtrip_preserves_order():
    with _temp_store_path():
        sr.save_stores(["Trafford", "Aberdeen", "Milton Keynes"])
        assert sr.load_stores() == ["Trafford", "Aberdeen", "Milton Keynes"]


def test_save_dedupes_case_insensitively_keeping_first():
    with _temp_store_path():
        sr.save_stores(["Trafford", "  trafford ", "Aberdeen", "TRAFFORD"])
        assert sr.load_stores() == ["Trafford", "Aberdeen"]


def test_save_drops_blank_rows():
    with _temp_store_path():
        sr.save_stores(["Trafford", "   ", "", "Aberdeen"])
        assert sr.load_stores() == ["Trafford", "Aberdeen"]


def test_save_preserves_aliases():
    with _temp_store_path():
        sr.save_stores(["Trafford"])
        data = json.loads(sr.STORE_DATA_PATH.read_text(encoding="utf-8"))
        assert data["aliases"] == sr.DEFAULT_ALIASES


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
