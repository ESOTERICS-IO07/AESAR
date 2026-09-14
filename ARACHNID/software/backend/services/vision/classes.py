from __future__ import annotations

from typing import Dict, List, Literal, Set

# ─────────────────────────────────────────────────────────────
# Authoritative Vision Classes — AESAR Master Contract v2.1
# ─────────────────────────────────────────────────────────────

# Canonical Machine-Readable Identifiers
PEST_BROWN_PLANTHOPPER = "brown_planthopper"
PEST_GREEN_LEAFHOPPER = "green_leafhopper"
PEST_YELLOW_STEM_BORER = "yellow_stem_borer"
PEST_COTTON_APHIDS = "cotton_aphids"
PEST_CHILLI_THRIPS = "chilli_thrips"
PEST_AMERICAN_BOLLWORM = "american_bollworm"

DEFENDER_LADYBIRD_BEETLE = "ladybird_beetle"
DEFENDER_LYCOSA_WOLF_SPIDER = "lycosa_wolf_spider"
DEFENDER_MIRID_BUG = "mirid_bug"
DEFENDER_CARABID_BEETLE = "carabid_beetle"
DEFENDER_GREEN_LACEWING = "green_lacewing"

CANONICAL_PESTS: List[str] = [
    PEST_BROWN_PLANTHOPPER,
    PEST_GREEN_LEAFHOPPER,
    PEST_YELLOW_STEM_BORER,
    PEST_COTTON_APHIDS,
    PEST_CHILLI_THRIPS,
    PEST_AMERICAN_BOLLWORM,
]

CANONICAL_DEFENDERS: List[str] = [
    DEFENDER_LADYBIRD_BEETLE,
    DEFENDER_LYCOSA_WOLF_SPIDER,
    DEFENDER_MIRID_BUG,
    DEFENDER_CARABID_BEETLE,
    DEFENDER_GREEN_LACEWING,
]

ALL_CANONICAL_CLASSES: Set[str] = set(CANONICAL_PESTS + CANONICAL_DEFENDERS)

CLASS_TO_CATEGORY: Dict[str, Literal["pest", "defender"]] = {
    **{p: "pest" for p in CANONICAL_PESTS},
    **{d: "defender" for d in CANONICAL_DEFENDERS},
}

# Contract Display Names
CANONICAL_DISPLAY_NAMES: Dict[str, str] = {
    PEST_BROWN_PLANTHOPPER: "Brown Planthopper (BPH)",
    PEST_GREEN_LEAFHOPPER: "Green Leafhopper (GLH)",
    PEST_YELLOW_STEM_BORER: "Yellow Stem Borer",
    PEST_COTTON_APHIDS: "Cotton Aphids",
    PEST_CHILLI_THRIPS: "Chilli Thrips",
    PEST_AMERICAN_BOLLWORM: "American Bollworm",
    DEFENDER_LADYBIRD_BEETLE: "Ladybird Beetle adult/larva",
    DEFENDER_LYCOSA_WOLF_SPIDER: "Lycosa/Wolf Spider",
    DEFENDER_MIRID_BUG: "Mirid Bug",
    DEFENDER_CARABID_BEETLE: "Carabid Beetle",
    DEFENDER_GREEN_LACEWING: "Green Lacewing",
}

# Aliases and variants mapped to canonical identifiers
ALIASES_TO_CANONICAL: Dict[str, str] = {
    # BPH
    "brown_planthopper": PEST_BROWN_PLANTHOPPER,
    "bph": PEST_BROWN_PLANTHOPPER,
    "brown planthopper": PEST_BROWN_PLANTHOPPER,
    "brown planthopper (bph)": PEST_BROWN_PLANTHOPPER,
    # GLH
    "green_leafhopper": PEST_GREEN_LEAFHOPPER,
    "glh": PEST_GREEN_LEAFHOPPER,
    "green leafhopper": PEST_GREEN_LEAFHOPPER,
    "green leafhopper (glh)": PEST_GREEN_LEAFHOPPER,
    # Stem Borer
    "yellow_stem_borer": PEST_YELLOW_STEM_BORER,
    "stem_borer": PEST_YELLOW_STEM_BORER,
    "yellow stem borer": PEST_YELLOW_STEM_BORER,
    "ysb": PEST_YELLOW_STEM_BORER,
    # Aphids
    "cotton_aphids": PEST_COTTON_APHIDS,
    "cotton_aphid": PEST_COTTON_APHIDS,
    "aphids": PEST_COTTON_APHIDS,
    "aphid": PEST_COTTON_APHIDS,
    "cotton aphids": PEST_COTTON_APHIDS,
    # Thrips
    "chilli_thrips": PEST_CHILLI_THRIPS,
    "chilli_thrip": PEST_CHILLI_THRIPS,
    "thrips": PEST_CHILLI_THRIPS,
    "thrip": PEST_CHILLI_THRIPS,
    "chilli thrips": PEST_CHILLI_THRIPS,
    # Bollworm
    "american_bollworm": PEST_AMERICAN_BOLLWORM,
    "bollworm": PEST_AMERICAN_BOLLWORM,
    "american bollworm": PEST_AMERICAN_BOLLWORM,
    "helicoverpa": PEST_AMERICAN_BOLLWORM,
    # Ladybird
    "ladybird_beetle": DEFENDER_LADYBIRD_BEETLE,
    "ladybird": DEFENDER_LADYBIRD_BEETLE,
    "ladybird beetle": DEFENDER_LADYBIRD_BEETLE,
    "ladybug": DEFENDER_LADYBIRD_BEETLE,
    "ladybird beetle adult/larva": DEFENDER_LADYBIRD_BEETLE,
    "ladybird beetle adult": DEFENDER_LADYBIRD_BEETLE,
    "ladybird beetle larva": DEFENDER_LADYBIRD_BEETLE,
    # Wolf Spider
    "lycosa_wolf_spider": DEFENDER_LYCOSA_WOLF_SPIDER,
    "wolf_spider": DEFENDER_LYCOSA_WOLF_SPIDER,
    "lycosa": DEFENDER_LYCOSA_WOLF_SPIDER,
    "spider": DEFENDER_LYCOSA_WOLF_SPIDER,
    "spiders": DEFENDER_LYCOSA_WOLF_SPIDER,
    "lycosa/wolf spider": DEFENDER_LYCOSA_WOLF_SPIDER,
    "wolf spider": DEFENDER_LYCOSA_WOLF_SPIDER,
    # Mirid Bug
    "mirid_bug": DEFENDER_MIRID_BUG,
    "mirid bug": DEFENDER_MIRID_BUG,
    "mirid": DEFENDER_MIRID_BUG,
    # Carabid Beetle
    "carabid_beetle": DEFENDER_CARABID_BEETLE,
    "carabid beetle": DEFENDER_CARABID_BEETLE,
    "carabid": DEFENDER_CARABID_BEETLE,
    "ground_beetle": DEFENDER_CARABID_BEETLE,
    # Green Lacewing
    "green_lacewing": DEFENDER_GREEN_LACEWING,
    "green lacewing": DEFENDER_GREEN_LACEWING,
    "lacewing": DEFENDER_GREEN_LACEWING,
}


def resolve_class_name(raw_name: str) -> str:
    """
    Resolves any model or user-provided class name to its canonical identifier.
    Returns the resolved canonical identifier if recognized, or stripped lowercase input.
    """
    cleaned = raw_name.strip().lower()
    return ALIASES_TO_CANONICAL.get(cleaned, cleaned)


def get_class_category(canonical_or_raw_name: str) -> Literal["pest", "defender"]:
    """
    Returns 'pest' or 'defender' for the given class name.
    Defaults to 'pest' if unknown.
    """
    canonical = resolve_class_name(canonical_or_raw_name)
    return CLASS_TO_CATEGORY.get(canonical, "pest")


def get_display_name(canonical_or_raw_name: str) -> str:
    """Returns the contract display name for a class."""
    canonical = resolve_class_name(canonical_or_raw_name)
    return CANONICAL_DISPLAY_NAMES.get(canonical, canonical.replace("_", " ").title())


def is_valid_vision_class(canonical_or_raw_name: str) -> bool:
    """Checks if the class is one of the 11 authoritative contract classes."""
    canonical = resolve_class_name(canonical_or_raw_name)
    return canonical in ALL_CANONICAL_CLASSES
