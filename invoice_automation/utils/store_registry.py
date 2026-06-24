"""Single source of truth for the recognised Menkind store names (and aliases).

The store list is what ``GenericExtractor`` validates extracted store candidates
against — a candidate is only shown if it snaps to a name here, otherwise the
card shows "Store: Unknown" (see ``_clean_town_or_empty``).

Persistence mirrors ``data/nominal_codes.json``: the canonical list lives in
``data/known_stores.json`` and is editable in-app (sidebar → "Store Names").
``DEFAULT_STORES`` / ``DEFAULT_ALIASES`` below are the shipped baseline and the
fallback used when the JSON is missing or unreadable, so the extractor always
has a usable list.

NOTE: on Streamlit Community Cloud the filesystem is ephemeral — in-app edits
last until the next reboot/redeploy. For a permanent change, edit
``data/known_stores.json`` in the repo (same as nominal codes).
"""

import json
import re
from pathlib import Path

STORE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "known_stores.json"

# Shipped baseline / fallback. Sourced from the real Maintenance PO workbook
# (data-sheet STORE columns + the two pivot tabs); "<store> PB" rows excluded and
# obvious source typos normalised. Display strings; matched case-insensitively.
DEFAULT_STORES = [
    "Aberdeen", "Basingstoke", "Birmingham", "Blackpool", "Bluewater Lower",
    "Bluewater Upper", "Braehead", "Brighton", "Bristol", "Bromley",
    "Cambridge", "Cardiff", "Chelmsford", "Clarks Village", "Colchester",
    "Cribbs", "Cwmbran", "Derby", "Doncaster", "Dundee", "Eastbourne",
    "Edinburgh", "Edinburgh Fort", "Glasgow Buchanan", "Gateshead",
    "Glasgow Braehead", "Glasgow Fort", "Glasgow Silverburn",
    "Glasgow St Enoch", "Gloucester Quays", "Guildford", "Hanley",
    "Hereford", "High Wycombe", "Hull", "Lakeside", "Leeds White Rose",
    "Leicester", "Liverpool", "Livingston", "Maidstone", "Manchester",
    "Meadowhall", "Meadowhall Lower", "Meadowhall Upper", "Merry Hill",
    "Milton Keynes", "Newcastle", "Nottingham", "Oxford", "Peterborough",
    "Portsmouth", "Reading", "Redditch", "Southampton",
    "Staines", "Stratford", "Swansea", "Trafford", "Warrington", "Watford",
    "Worcester",
]

# Variant spellings that appear on invoices/source data but are not the canonical
# store name. Keys are matched as whole-store candidates (lower-cased); values are
# the canonical display name (must appear in the store list). Not editable in-app.
DEFAULT_ALIASES = {
    "silverburn": "Glasgow Silverburn",
}


def _read_json() -> dict:
    """Return the parsed known_stores.json, or {} if missing/unreadable."""
    try:
        if STORE_DATA_PATH.exists():
            with open(STORE_DATA_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def load_stores() -> list[str]:
    """Return the recognised store list (JSON if valid, else DEFAULT_STORES)."""
    stores = _read_json().get("stores")
    if isinstance(stores, list):
        cleaned = [str(s).strip() for s in stores if str(s).strip()]
        if cleaned:
            return cleaned
    return list(DEFAULT_STORES)


def load_aliases() -> dict[str, str]:
    """Return the alias→canonical map (JSON if present, else DEFAULT_ALIASES)."""
    aliases = _read_json().get("aliases")
    if isinstance(aliases, dict):
        return {str(k).strip().lower(): str(v).strip() for k, v in aliases.items()}
    return dict(DEFAULT_ALIASES)


def _norm_words(s: str) -> list[str]:
    """Lower-cased word tokens of a string (letters/apostrophes only)."""
    return re.findall(r"[a-z']+", s.lower())


def clean_store(
    candidate: str,
    stores: list[str] | None = None,
    aliases: dict[str, str] | None = None,
) -> str:
    """Snap a raw store candidate to a known store name, or return "".

    This is the single source of store-name validation, shared by every
    extractor (the generic one calls it during extraction; the routing layer
    applies it to all extractors' output). A candidate is only accepted when it
    matches a known store — never a street, building, address blob, or company:

    1. Strip UK postcodes and surrounding punctuation/whitespace.
    2. Exact whole-string match against a known store/alias → canonical name.
    3. Else the longest known store name appearing as a contiguous run of words
       inside the candidate (so "…Eden Centre … High Wycombe" → "High Wycombe",
       and "Glasgow Fort" beats a bare "Glasgow").
    4. No known store found → "" ("if the app is not sure, no store is shown").

    Passing ``stores``/``aliases`` avoids re-reading the JSON; omit them to load
    the current registry values.
    """
    if not candidate:
        return ""
    if stores is None:
        stores = load_stores()
    if aliases is None:
        aliases = load_aliases()

    cleaned = re.sub(
        r"[A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2}", "", candidate, flags=re.IGNORECASE
    )
    cleaned = cleaned.strip(" \t,.-–—/").strip()
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return ""

    words = _norm_words(cleaned)
    if not words:
        return ""

    matchable = [(s, _norm_words(s)) for s in stores]
    matchable += [(canonical, _norm_words(alias)) for alias, canonical in aliases.items()]
    known = sorted(matchable, key=lambda kv: len(kv[1]), reverse=True)

    for canonical, ktokens in known:
        if words == ktokens:
            return canonical
    for canonical, ktokens in known:
        n = len(ktokens)
        for i in range(len(words) - n + 1):
            if words[i : i + n] == ktokens:
                return canonical
    return ""


def save_stores(stores: list[str]) -> None:
    """Persist the store list to known_stores.json (aliases preserved).

    De-duplicates case-insensitively while preserving the given order.
    """
    seen: set[str] = set()
    cleaned: list[str] = []
    for s in stores:
        name = str(s).strip()
        key = name.lower()
        if name and key not in seen:
            cleaned.append(name)
            seen.add(key)
    STORE_DATA_PATH.parent.mkdir(exist_ok=True)
    with open(STORE_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({"stores": cleaned, "aliases": load_aliases()}, f, indent=2)
