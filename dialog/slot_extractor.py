import re
from dataclasses import dataclass
from typing import Optional
from Levenshtein import distance as levenshtein_distance
from dialog.ontology import ONTOLOGY
from dialog.semantic_similarity import find_semantic_match

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


def extract_by_keyword(text: str) -> list[SlotResult]:
    """
    Extract an ontology term from the utterance by keyword matching.
    """
    results = []
    text = text.lower().strip()

    food_pattern = r"\b(" + "|".join(map(re.escape, ONTOLOGY["food"])) + r")\s+food\b"

    match = re.search(food_pattern, text)

    if match:
        results.append(SlotResult(
            slot="food",
            value=match.group(1),
            method="keyword",
            needs_confirmation=False,
            original_value=match.group(1),
        ))
    else:
        for value in ONTOLOGY["food"]:
            if re.search(r"\b" + re.escape(value) + r"\b", text):
                results.append(SlotResult(
                    slot="food",
                    value=value,
                    method="keyword",
                    needs_confirmation=False,
                    original_value=value,
                ))
                break

    for value in ONTOLOGY["price"]:
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            results.append(SlotResult(
                slot="price",
                value=value,
                method="keyword",
                needs_confirmation=False,
                original_value=value,
            ))
            break

    for value in ONTOLOGY["area"]:
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            results.append(SlotResult(
                slot="area",
                value=value,
                method="keyword",
                needs_confirmation=False,
                original_value=value,
            ))
            break

    return results


def extract_by_levenshtein(candidate: str, slot: str, max_distance: int = 2)-> Optional[SlotResult]:
    """
    Fallback to recover a slot value using Levenshtein edit distance when keyword matching does not work.
    When Levenshtein returns a value that is not an exact match, it requires confirmation.
    """
    print("debug find levenshtein")
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


def extract_candidates(text: str) -> list[tuple[str, str]]:
    """
    Identify the likely slot and candidate value from user's utterance.
    """
    text = text.lower().strip()
    candidates = []

    tokens = text.split()

    if len(tokens) == 1:
        # one word reply
        word = tokens[0]
        candidates.append((word, "price"))
        candidates.append((word, "food"))
        candidates.append((word, "area"))

    price_patterns = [
        r"\b(cheap|moderate|expensive)\b",
        r"\b(cheap|moderately|moderate|expensive)\s+priced\b",
        r"\b(cheap|moderate|expensive)\s+price\s+range\b",
        r"\bin\s+(any)\s+price\b",
    ]
    for pattern in price_patterns:
        for match in re.finditer(pattern, text):
            candidates.append((match.group(1), "price"))

    area_patterns = [
        r"\bin\s+(?:the\s+)?([a-z]+)(?:\s+area)?\b",
        r"\b(?:in|on)\s+the\s+([a-z]+)\s+(?:part|area)\b",
        r"\bin\s+(?:the\s+)?(north|south|east|west|centre|center)\b",
        r"\b(north|south|east|west|centre|center)\s+part\s+of\s+town\b",
        r"\b(north|south|east|west|centre|center)\s+area\b",
        r"\bin\s+(any)\s+area\b",
    ]
    for pattern in area_patterns:
        for match in re.finditer(pattern, text):
            candidates.append((match.group(1), "area"))

    food_patterns = [
        r"\b(\w+)\s+food\b",
        r"\b(\w+)\s+cuisine\b",
        r"\bin\s+(any)\s+food\b",
    ]
    for pattern in food_patterns:
        for match in re.finditer(pattern, text):
            candidates.append((match.group(1), "food"))

    restaurant_pattern = r"\b(\w+)\s+restaurant\b"
    for match in re.finditer(restaurant_pattern, text):
        candidate = match.group(1)

        if candidate in ONTOLOGY["food"]:
            candidates.append((candidate, "food"))

    return candidates


def extract_by_semantic(candidate: str, slot: str, threshold: float = 0.7) -> Optional[SlotResult]:
    """
    Fallback to recover a slot value using semantic similarity when keyword matching does not work.
    The candidate is compared against the ontology values for the specified slot using DistilBERT embeddings.
    Returns None if the best semantic match is below the similarity threshold.
    """
    if slot not in ONTOLOGY:
        raise ValueError(f"Unknown slot: {slot}")

    result = find_semantic_match(candidate=candidate, slot=slot, threshold=threshold)

    if result is None:
        return None

    best_value, score = result

    return SlotResult(
        slot=slot,
        value=best_value,
        method="semantic",
        needs_confirmation=False,
        original_value=candidate,
    )


def extract_slots(
    text: str,
    fallback: str = "levenshtein",
    semantic_threshold: float = 0.7,
) -> list[SlotResult]:
    """
    Extract all slots from a user utterance.
    Keyword matching is attempted first.
    If no exact keyword match is found for a candidate, the configured fallback "levenshtein" or "semantic" can be used.

    Returns:
        A list of SlotResult objects.
    """
    results = []
    keyword_results = extract_by_keyword(text)

    if keyword_results:
        results.extend(keyword_results)

    normalized_text = text.lower().strip()

    wildcards = [
        ("food", ["any food", "any cuisine"]),
        ("price", ["any price", "any pricing"]),
        ("area", ["any area", "anywhere"]),
    ]

    for slot, phrases in wildcards:
        if any(phrase in normalized_text for phrase in phrases):
            results.append(
                SlotResult(
                    slot=slot,
                    value="any",
                    method="keyword",
                    needs_confirmation=False,
                    original_value="any",
                )
            )

    candidates = extract_candidates(text)

    for candidate, slot in candidates:
        # Check whether this candidate/slot was already extracted by keyword matching.
        already_found = any(
            slot_result.slot == slot
            and (slot_result.value or "").lower() == candidate.strip().lower()
            for slot_result in results
        )
        if already_found:
            continue

        if fallback == "levenshtein":
            result = extract_by_levenshtein(candidate=candidate, slot=slot)
        elif fallback == "semantic":
            result = extract_by_semantic(candidate=candidate, slot=slot, threshold=semantic_threshold)
        else:
            raise ValueError(
                f"Unknown slot extraction method: {fallback}. Expected 'levenshtein' or 'semantic'."
            )

        if result is not None:
            results.append(result)

    return results