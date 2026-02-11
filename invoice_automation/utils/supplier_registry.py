"""
Single source of truth for supplier identification.

Maps text markers (keywords found in invoice text or filenames) to supplier
metadata. Used by web_app.py for extractor routing and by GenericExtractor
for supplier name/type identification.
"""

# Each entry: (text_markers, filename_markers, supplier_name, supplier_type)
# text_markers: list of lowercase substrings to search in invoice text
# filename_markers: list of lowercase substrings to search in filename
# Checked in order - first match wins, so put more specific entries first.
SUPPLIER_REGISTRY: list[tuple[list[str], list[str], str, str]] = [
    # Specific extractors (AAW, CJL, Amazon, APS)
    (["aaw national"], ["aaw"], "AAW National Maintenance", "AAW"),
    (["cjl group"], ["cjl"], "CJL Associates", "CJL"),
    (["amazon business"], ["amazon"], "Amazon", "AMAZON"),
    (["automatic protection"], ["aps"], "APS Fire Systems", "APS"),
    # Generic extractor suppliers
    (["compco fire", "compco"], ["compco"], "Compco Fire Systems", "COMPCO"),
    (["sunbelt"], ["sunbelt"], "Sunbelt Rentals", "SUNBELT"),
    (["maxwell jones", "maxwelljones"], [], "Maxwell Jones", "MAXWELL_JONES"),
    (["metro security"], [], "Metro Security", "METRO_SECURITY"),
    (["metsafe"], [], "MetSafe", "METRO_SECURITY"),
    (
        ["store maintenance", "reactive on call"],
        [],
        "Store Maintenance",
        "STORE_MAINTENANCE",
    ),
    (["lampshoponline", "lampshop"], [], "LampShopOnline", "LAMPSHOP"),
    (["ilux"], [], "ILUX Lighting", "ILUX"),
    (["aura"], [], "Aura Air Conditioning", "AURA"),
]


def identify_supplier(text: str, filename: str = "") -> tuple[str, str]:
    """
    Identify supplier from invoice text and/or filename.

    Returns:
        (supplier_name, supplier_type) tuple.
        Falls back to ("Unknown Supplier", "GENERIC") if no match.
    """
    text_lower = text.lower()
    filename_lower = filename.lower()

    for text_markers, filename_markers, name, stype in SUPPLIER_REGISTRY:
        for marker in text_markers:
            if marker in text_lower:
                return name, stype
        for marker in filename_markers:
            if marker in filename_lower:
                return name, stype

    return "Unknown Supplier", "GENERIC"
