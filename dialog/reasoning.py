# dialog/reasoning.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: int
    antecedent: tuple  # e.g. (("pricerange", "cheap"), ("food quality", "good food"))
    consequent: str  # e.g. "touristic"
    value: bool
    description: str


RULES = [
    Rule(
        1,
        (("pricerange", "cheap"), ("food quality", "good")),
        "touristic",
        True,
        "a cheap restaurant with good food attracts tourists",
    ),
    Rule(
        2,
        (("food", "romanian"),),
        "touristic",
        False,
        "Romanian cuisine is unknown for most tourists and they prefer familiar food",
    ),
    Rule(
        3,
        (("crowdedness", "busy"),),
        "assigned_seats",
        True,
        "in a busy restaurant the waiter decides where you sit",
    ),
    Rule(
        4,
        (("length of stay", "long"),),
        "children",
        False,
        "spending a long time in a restaurant is not advised when taking children",
    ),
    Rule(
        5,
        (("crowdedness", "busy"),),
        "romantic",
        False,
        "a busy restaurant is not romantic",
    ),
    Rule(
        6,
        (("length of stay", "long"),),
        "romantic",
        True,
        "spending a long time in a restaurant is romantic",
    ),
]

ADDITIONAL_REQUIREMENT_KEYWORDS = {
    "touristic": ["touristic", "tourist"],
    "assigned_seats": ["assigned seats", "assigned seating"],
    "children": ["children", "child", "kids", "family friendly"],
    "romantic": ["romantic", "romance", "date night"],
}
NEGATION_WORDS = {"not", "no", "don't", "dont"}

def rule_fires(rule: Rule, restaurant: dict) -> bool:
    return all(restaurant.get(attr) == val for attr, val in rule.antecedent)


def apply_rules(restaurant: dict, rules=RULES) -> dict[str, list[Rule]]:
    """Group every rule that fires, by which consequent it affects."""
    fired = {}
    for rule in rules:
        if rule_fires(rule, restaurant):
            fired.setdefault(rule.consequent, []).append(rule)
    return fired


def resolve_property(fired_rules, strategy="positive_wins"):
    if not fired_rules:
        return None, None, None  # value, explanation, contradiction_note

    true_rules = [r for r in fired_rules if r.value is True]
    false_rules = [r for r in fired_rules if r.value is False]

    if true_rules and false_rules:
        # genuine contradiction — both a True and a False rule fired
        if strategy == "positive_wins":
            chosen, losing = true_rules[0], false_rules[0]
        elif strategy == "negative_wins":
            chosen, losing = false_rules[0], true_rules[0]
        elif strategy == "majority":
            if len(true_rules) > len(false_rules):
                chosen, losing = true_rules[0], false_rules[0]
            elif len(false_rules) > len(true_rules):
                chosen, losing = false_rules[0], true_rules[0]
            else:
                return None, None, "conflicting evidence, no majority"
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        return chosen.value, chosen.description, losing.description

    chosen = true_rules[0] if true_rules else false_rules[0]
    return chosen.value, chosen.description, None  # no contradiction, nothing to disclose


def derive_properties(restaurant, strategy="positive_wins"):
    derived = {}
    for prop, fired_rules in apply_rules(restaurant).items():
        value, explanation, contradiction_note = resolve_property(fired_rules, strategy=strategy)
        if value is not None:
            derived[prop] = (value, explanation, contradiction_note)
    return derived



def parse_additional_requirement(text: str):
    normalized = text.lower().strip()
    for prop, keywords in ADDITIONAL_REQUIREMENT_KEYWORDS.items():
        if any(k in normalized for k in keywords):
            wants_it = not any(neg in normalized.split() for neg in NEGATION_WORDS)
            return prop, wants_it
    return None, None