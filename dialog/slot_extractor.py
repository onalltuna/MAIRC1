import re
from dataclasses import dataclass
from typing import Optional
from Levenshtein import distance as levenshtein_distance

# Define ONTOLOGY terms TODO：maybe need to add more terms and are these three slots enough?
ONTOLOGY = {
    "food": [
        "african",
        "asian",
        "british",
        "chinese",
        "french",
        "indian",
        "italian",
        "japanese",
        "mediterranean",
        "mexican",
        "portuguese",
        "spanish",
        "thai",
        "turkish",
    ],
    "price": [
        "cheap",
        "moderate",
        "expensive",
    ],
    "area": [
        "centre",
        "north",
        "south",
        "east",
        "west",
    ],
}

@dataclass
class SlotResult:
    slot: Optional[str] = None
    value: Optional[str] = None

    # How the value was found:
    # "keyword", "levenshtein", "semantic", or None
    method: Optional[str] = None

    # If the value needs confirmation
    needs_confirmation: bool = False

    # Original value detected from the user
    original_value: Optional[str] = None


def extract_by_keyword(text: str) -> Optional[SlotResult]:
    """
    Extract an ontology term from the utterance by keyword matching.
    """

    text = text.lower().strip()

    # Food
    # Ex. "I want Italian food"
    food_pattern = r"\b(" + "|".join(map(re.escape, ONTOLOGY["food"])) + r")\s+food\b"

    match = re.search(food_pattern, text)

    if match:
        return SlotResult(
            slot="food",
            value=match.group(1),
            method="keyword",
            needs_confirmation=False,
            original_value=match.group(1),
        )

    # Ex. "I want Italian"
    for value in ONTOLOGY["food"]:
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            return SlotResult(
                slot="food",
                value=value,
                method="keyword",
                needs_confirmation=False,
                original_value=value,
            )

    # Price
    for value in ONTOLOGY["price"]:
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            return SlotResult(
                slot="price",
                value=value,
                method="keyword",
                needs_confirmation=False,
                original_value=value,
            )

    # Area
    for value in ONTOLOGY["area"]:
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            return SlotResult(
                slot="area",
                value=value,
                method="keyword",
                needs_confirmation=False,
                original_value=value,
            )

    return None


def extract_by_levenshtein(candidate: str, slot: str, max_distance: int = 2)-> Optional[SlotResult]:
    """
        Fallback to recover a slot value using Levenshtein edit distance when keyword matching does not work.

        When Levenshtein returns a value that is not an exact match, it requires confirmation.
        """
    if slot not in ONTOLOGY:
        raise ValueError(f"Unknown slot: {slot}")

    candidate = candidate.strip().lower()
    best_value = None
    best_distance = float("inf")

    for value in ONTOLOGY[slot]:
        d = levenshtein_distance(candidate, value.lower())

        if d < best_distance:
            best_distance = d
            best_value = value

    if best_distance > max_distance:
        return None

    return SlotResult(
        slot=slot,
        value=best_value,
        method="levenshtein",
        needs_confirmation=(candidate != best_value.lower()),
        original_value=candidate,
    )


def extract_candidate(text: str) -> Optional[tuple[str, str]]:
    """
    Identify the likely slot and candidate value from user's utterance.
    """

    text = text.lower().strip()

    # Example: "I want Spenish food"
    match = re.search(r"\b(\w+)\s+food\b", text)

    if match:
        return match.group(1), "food"

    # TODO:Add appropriate patterns for price/area/etc. here.

    return None


def extract_slot(
    text: str,
    fallback: str = "levenshtein"
) -> Optional[SlotResult]:
    """
    Main slot extraction function.

    Currently fallback="levenshtein" TODO: add semantic similarity
    """
    result = extract_by_keyword(text)

    if result is not None:
        return result

    if fallback == "levenshtein":
        candidate_info = extract_candidate(text)
        if candidate_info is None:
            return None

        candidate, slot = candidate_info

        return extract_by_levenshtein(
            candidate=candidate,
            slot=slot
        )

    raise ValueError(
        f"Unknown slot extraction method: {fallback}"
    )