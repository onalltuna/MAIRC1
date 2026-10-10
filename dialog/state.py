from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DialogConfig:
    slot_fallback: str = "levenshtein"
    reasoning_transparency: bool = True

class DialogStateName:
    WELCOME = "WELCOME"
    COLLECT_PREFERENCES = "COLLECT_PREFERENCES"
    CONFIRM_SLOT = "CONFIRM_SLOT"
    LOOKUP = "LOOKUP"
    RECOMMEND = "RECOMMEND"
    ALTERNATIVE = "ALTERNATIVE"
    ADDITIONAL_REQUIREMENT = "ADDITIONAL_REQUIREMENT"
    OFFER_DETAILS = "OFFER_DETAILS"
    NO_MATCH = "NO_MATCH"
    OFFER_PREFERENCE_CHANGE = "OFFER_PREFERENCE_CHANGE"
    END = "END"

@dataclass
class DialogState:

    # Main dialog state
    state: str = "WELCOME"

    # User preferences
    food: Optional[str] = None
    price: Optional[str] = None
    area: Optional[str] = None

    # Pending slot confirmations
    pending_confirmations: list = field(default_factory=list)

    # Restaurant candidates
    restaurants: list = field(default_factory=list)

    # Restaurants already presented
    alternatives: list = field(default_factory=list)

    # Current restaurant
    current_restaurant: Optional[dict] = None

    # restaurants already recommended / declined
    shown: set = field(default_factory=set)       # cleared when preferences change
    rejected: set = field(default_factory=set)    # never cleared

    # additional requirement
    additional_requirement: Optional[dict] = None
    additional_requirement_asked: bool = False

    # Whether the additional requirement question has been asked already
    additional_requirement_asked: bool = False

    # Last system response, useful for repeat
    last_response: Optional[str] = None

@dataclass
class UserInput:
    text: str
    dialog_act: str