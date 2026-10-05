import random
from dataclasses import dataclass
from dialog.slot_extractor import extract_slots
from dialog.responses import response
from dialog.state import DialogState, DialogStateName
from dialog.restaurant_lookup import find_restaurants
from dialog.reasoning import derive_properties, parse_additional_requirement, apply_rules
import re


@dataclass
class UserInput:
    text: str
    dialog_act: str

SLOT_TO_RESTAURANT_FIELD = {
    "food": "food",
    "price": "pricerange",  
    "area": "area",
}

NO_PREFERENCE_PHRASES = {
    "any",
    "i don't care",
    "i dont care",
    "dont care",
    "don't care",
    "doesn't matter",
    "does not matter",
    "whatever",
    "anything",
    "no preference",
    "i have no preference",
    "it doesn't matter",
}


def is_no_preference(normalized_text: str) -> bool:
    # exact match — covers short standalone answers like "any" or "whatever"
    if normalized_text in NO_PREFERENCE_PHRASES:
        return True

    for phrase in NO_PREFERENCE_PHRASES:
        if phrase == "any":
            # "any" needs a word-boundary check — a plain substring
            # check would incorrectly match inside words like "many"
            if re.search(r"\bany\b", normalized_text):
                return True
        elif phrase in normalized_text:
            return True

    return False


def handle_restaurant_confirmation(state, text, config):
    restaurant = state.current_restaurant

    if restaurant is None:
        system_response = response("nomatch")
        state.last_response = system_response
        return state, system_response

    results = extract_slots(text, fallback=config.slot_fallback)

    if not results:
        system_response = response("confirm_unclear")
        state.last_response = system_response
        return state, system_response

    # handle the first slot the user asked about
    result = results[0]
    field = SLOT_TO_RESTAURANT_FIELD.get(result.slot, result.slot)
    actual_value = restaurant.get(field)

    if actual_value == result.value:
        system_response = response("confirm_yes")
    else:
        system_response = response(
            "confirm_no",
            field=field,
            actual_value=actual_value,
        )

    state.last_response = system_response
    return state, system_response

def has_multiple_matches(state) -> bool:
    """
    True when more than one restaurant matches the current food/price/area
    preferences — i.e. asking about additional requirements is actually
    useful for narrowing down a choice. If there are 0 or 1 matches,
    there's nothing to narrow, so we skip straight to lookup.
    """
    matches = find_restaurants(food=state.food, price=state.price, area=state.area)
    return len(matches) > 1


def handle_additional_requirements(state, text, act, config):
    normalized = text.lower().strip()
    no_requirement = {"no", "n", "none", "nope", "no thanks", "nothing"}

    if act in {"negate", "deny"} or normalized in no_requirement:
        state.additional_requirement = None
    else:
        prop, desired = parse_additional_requirement(text)
        state.additional_requirement = {"property": prop, "value": desired} if prop else None

    state.additional_requirement_asked = True   # separate field — doesn't clobber the value above
    state.state = DialogStateName.LOOKUP
    return transition(state, UserInput(text="", dialog_act="internal_lookup"), config)


def handle_welcome(state, text, act, config):
    if act == "inform":
        return handle_preferences(state, text, act, config)

    state.state = DialogStateName.COLLECT_PREFERENCES
    system_response = ask_for_missing_slot(state)
    state.last_response = system_response
    return state, system_response


def all_preferences_known(state) -> bool:
    """
    Return True when all required restaurant preferences
    have been collected.
    """

    return (
        state.food is not None
        and state.price is not None
        and state.area is not None
    )


def ask_for_missing_slot(state):

    if state.food is None:
        return response("askfood")

    if state.area is None:
        return response("askarea")

    if state.price is None:
        return response("askpricerange")

    return ""


def get_missing_slot(state):
    if state.food is None:
        return "food"

    if state.area is None:
        return "area"

    if state.price is None:
        return "price"

    return None


def reset_restaurant_results(state):
    """
    Clear restaurant-specific results after the user's preferences have changed.
    """
    state.current_restaurant = None
    state.alternatives = []


def handle_preferences(
    state,
    text,
    act,
    config,
):
    normalized_text = text.lower().strip()
    missing_slot = get_missing_slot(state)
    
    # no_preference = {"any", "i don't care", "i dont care", "dont care", "doesn't matter", "does not matter", "whatever", "anything", "no preference", "i have no preference", "it doesn't matter"}

    results = extract_slots(text, fallback=config.slot_fallback, expected_slot=missing_slot)

    # The classifier may have mislabeled an utterance that still
    # contains a usable preference (e.g. "How about Lebanese food"
    # classified as "reqalts"). Only bail out to a generic re-ask when
    # we truly found nothing usable.
    if act != "inform" and not results and not is_no_preference(normalized_text):
        system_response = ask_for_missing_slot(state)
        state.last_response = system_response
        return state, system_response

    if not results and is_no_preference(normalized_text):
        if missing_slot is not None:
            setattr(state, missing_slot, "any")
            if all_preferences_known(state):
                if not state.additional_requirement and has_multiple_matches(state):
                    state.state = DialogStateName.ADDITIONAL_REQUIREMENT
                    system_response = response("ask_additional")
                    state.last_response = system_response
                    return state, system_response

                state.state = DialogStateName.LOOKUP
                return transition(state, UserInput(text="", dialog_act="internal_lookup"), config)

            system_response = ask_for_missing_slot(state)
            state.last_response = system_response
            return state, system_response



    # Nothing was extracted, but we were specifically expecting a value
    # for `missing_slot` — the user likely gave an unrecognized preference.
    if not results and missing_slot is not None:
        system_response = response("unrecognized_preference")
        state.state = DialogStateName.COLLECT_PREFERENCES
        state.last_response = system_response
        return state, system_response

    changed_preferences = False

    for result in results:

        if result.needs_confirmation:
            state.pending_confirmations.append(result)

        else:
            old_value = getattr(state, result.slot, None)

            if old_value != result.value:
                changed_preferences = True

            setattr(
                state,
                result.slot,
                result.value,
            )

    if changed_preferences:
        reset_restaurant_results(state)

    # --------------------------------
    # Need confirmation?
    # --------------------------------

    if state.pending_confirmations:

        state.state = DialogStateName.CONFIRM_SLOT

        result = state.pending_confirmations[0]

        system_response = generate_confirmation(result)

        state.last_response = system_response

        return state, system_response

    # Check whether all preferences are known
    if all_preferences_known(state):
        if not state.additional_requirement and has_multiple_matches(state):
            state.state = DialogStateName.ADDITIONAL_REQUIREMENT
            system_response = response("ask_additional")
            state.last_response = system_response
            return state, system_response

        # already asked earlier in the conversation — skip straight to lookup
        state.state = DialogStateName.LOOKUP
        return transition(state, UserInput(text="", dialog_act="internal_lookup"), config)

        return transition(
            state,
            UserInput(
                text="",
                dialog_act="internal_lookup",
            ),
            config,
        )

    # --------------------------------
    # Ask for missing preference
    # --------------------------------

    system_response = ask_for_missing_slot(state)

    state.state = DialogStateName.COLLECT_PREFERENCES
    state.last_response = system_response

    return state, system_response


def generate_confirmation(result):
    """
    Generate a confirmation response for an approximate slot match.
    """

    if result.slot == "food":
        return response(
            "confirmfoodtype",
            givenfoodtype=result.original_value,
            correctedfoodtype=result.value,
        )

    if result.slot == "price":
        return response(
            "confirmpricerange",
            givenpricerange=result.original_value,
            correctedpricerange=result.value,
        )

    if result.slot == "area":
        return response(
            "confirmarea",
            givenarea=result.original_value,
            correctedarea=result.value,
        )

    # Generic fallback
    return response(
        "confirmslot",
        givenslot=result.original_value,
        correctedslot=result.value,
    )


def handle_confirmation(
    state,
    text,
    act,
    config,
):
    if not state.pending_confirmations:
        state.state = DialogStateName.COLLECT_PREFERENCES

        system_response = ask_for_missing_slot(state)

        state.last_response = system_response

        return state, system_response

    result = state.pending_confirmations[0]

    # --------------------------------
    # User accepted the suggestion
    # --------------------------------

    if act == "affirm" or text in {
        "yes",
        "y",
        "yeah",
        "correct",
    }:

        old_value = getattr(state, result.slot, None)

        setattr(
            state,
            result.slot,
            result.value,
        )

        if old_value != result.value:
            reset_restaurant_results(state)

        state.pending_confirmations.pop(0)

    # --------------------------------
    # User rejected the suggestion
    # --------------------------------

    elif act in {"deny", "negate"} or text in {
        "no",
        "n",
        "nope",
        "wrong",
    }:

        state.pending_confirmations.pop(0)

    # --------------------------------
    # Unknown confirmation response
    # --------------------------------

    else:
        system_response = response("confirmyesno")

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # More confirmations?
    # --------------------------------

    if state.pending_confirmations:

        next_result = state.pending_confirmations[0]

        system_response = generate_confirmation(
            next_result
        )

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # All confirmations finished
    # --------------------------------

    if all_preferences_known(state):

        state.state = DialogStateName.LOOKUP

        return transition(
            state,
            UserInput(
                text="",
                dialog_act="internal_lookup",
            ),
            config,
        )

    # --------------------------------
    # Some preferences are still missing
    # --------------------------------

    state.state = DialogStateName.COLLECT_PREFERENCES

    system_response = ask_for_missing_slot(state)

    state.last_response = system_response

    return state, system_response



def handle_lookup(state, config):
    matches = find_restaurants(food=state.food, price=state.price, area=state.area)

    if state.additional_requirement:
        prop = state.additional_requirement["property"]
        desired = state.additional_requirement["value"]

        filtered = []
        for r in matches:
            derived = derive_properties(r, strategy=config.reasoning_strategy)
            if prop in derived and derived[prop][0] == desired:
                r = dict(r)
                r["_reasoning_property"] = prop
                r["_reasoning_explanation"] = derived[prop][1]
                filtered.append(r)
        matches = filtered

    if not matches:
        state.state = DialogStateName.NO_MATCH
        system_response = response("nomatch", food=state.food, area=state.area, pricerange=state.price)
        state.last_response = system_response
        return state, system_response

    selected = random.choice(matches)
    state.current_restaurant = selected
    state.alternatives = [r for r in matches if r != selected]
    state.state = DialogStateName.RECOMMEND
    return transition(state, UserInput(text="", dialog_act="internal_recommend"), config)


def generate_recommendation(restaurant, show_reasoning=True):
    if restaurant is None:
        return response("nomatch")

    base = response(
        "recommend",
        restaurantname=restaurant["restaurantname"],
        food=restaurant["food"],
        area=restaurant["area"],
        pricerange=restaurant["pricerange"],
    )

    explanation = restaurant.get("_reasoning_explanation")
    if show_reasoning and explanation:
        prop = restaurant["_reasoning_property"].replace("_", " ")
        base += f" The restaurant is {prop} because {explanation}."

        note = restaurant.get("_reasoning_contradiction")
        if note:
            base += f" (Note: one rule suggested otherwise - {note}.)"

    return base

def handle_restaurant_request(state, text):
    restaurant = state.current_restaurant

    if restaurant is None:
        system_response = response("nomatch")
        state.last_response = system_response
        return state, system_response

    text = text.lower().strip()

    if any(word in text for word in {"address", "addr"}):
        address = restaurant.get("addr")
        if address:
            system_response = response(
                "address",
                restaurantname=restaurant["restaurantname"],
                address=restaurant["addr"],
            )
        else:
            system_response = response("restaurant_info_unknown", restaurantname=restaurant["restaurantname"])

    elif any(word in text for word in {"postcode", "post code", "postal"}):
        postcode = restaurant.get("postcode")
        if postcode:
            system_response = response(
                "postcode",
                restaurantname=restaurant["restaurantname"],
                postcode=restaurant["postcode"],
            )
        else:
            system_response = response("restaurant_info_unknown", info = "postcode",restaurantname=restaurant["restaurantname"])

    elif any(word in text for word in {"phone", "telephone", "number"}):
        phone = restaurant.get("phone")
        if phone:
            system_response = response(
                "phone",
                restaurantname=restaurant["restaurantname"],
                phone=restaurant["phone"],
            )
        else:
            system_response = response("restaurant_info_unknown", restaurantname=restaurant["restaurantname"])


    else:
        system_response = response(
            "restaurant_info",
            restaurantname=restaurant["restaurantname"],
        )

    state.last_response = system_response

    return state, system_response

def handle_recommendation(state, text, act, config):

    if act in {"reqalts", "alternative"}:
        # The classifier may have mislabeled a new preference as a
        # request for "another one from the same list" (e.g. "How
        # about Chinese food?" misclassified as "reqalts"). Check for
        # extractable slot content before falling back to alternatives.
        missing_slot = get_missing_slot(state)
        extracted = extract_slots(text, fallback=config.slot_fallback, expected_slot=missing_slot)

        if extracted:
            state.state = DialogStateName.COLLECT_PREFERENCES
            return handle_preferences(state, text, "inform", config)

        state.state = DialogStateName.ALTERNATIVE
        return handle_alternative(state, act, config)

    if act == "request":
        return handle_restaurant_request(state, text)

    if act in {"bye", "thankyou"}:
        state.state = DialogStateName.END
        system_response = response("goodbye")
        state.last_response = system_response
        return state, system_response

    system_response = generate_recommendation(state.current_restaurant, show_reasoning=config.reasoning_transparency)
    state.last_response = system_response
    return state, system_response

def handle_alternative(state, act, config):
    """
    Handle a request for an alternative restaurant.

    Uses the restaurants already found for the current
    set of preferences.
    """

    if not state.alternatives:
        state.state = DialogStateName.OFFER_PREFERENCE_CHANGE
        system_response = response("offer_preference_change")
        state.last_response = system_response

        return state, system_response

    # Take another restaurant
    alternative = state.alternatives.pop(0)

    # Make it the current restaurant
    state.current_restaurant = alternative

    state.state = DialogStateName.RECOMMEND

    system_response = response(
        "alternative",
        restaurantname=alternative["restaurantname"],
    )

    state.last_response = system_response

    return state, system_response

def handle_no_match(
    state,
    text,
    act,
    config,
):
    """
    Handle the case where no restaurant matches
    the user's current preferences.
    """
    missing_slot = get_missing_slot(state)
    extracted = extract_slots(
        text,
        fallback=config.slot_fallback,
        expected_slot=missing_slot,
    )

    if extracted:
        return handle_preferences(
            state,
            text,
            "inform",
            config,
        )

    if act in {"reqalts", "alternative"}:
        # User asks for another restaurant
        system_response = response("noalternative")

        state.last_response = system_response

        return state, system_response

    if act == "request":
        # User asks about the current restaurant
        return handle_restaurant_request(
            state,
            text,
        )

    if act == "inform":
        # User provides a new/changed preference.
        return handle_preferences(
            state,
            text,
            act,
            config,
        )

    if act == 'ack':
        system_response = response("acknowledge")

        state.last_response = system_response

        return state, system_response

    system_response = response("nomatch",config)

    state.last_response = system_response

    return state, system_response

def handle_offer_preference_change(
    state,
    text,
    act,
    config,
):
    """
    Handle the state where all restaurants for the current
    preferences have been exhausted.

    The user may:
      - change a preference
      - ask for information about the current restaurant
      - decline / end the conversation
      - ask to repeat
    """

    # --------------------------------
    # User wants to change preferences
    # --------------------------------

    if act == "inform":
        state.state = DialogStateName.COLLECT_PREFERENCES

        return handle_preferences(
            state,
            text,
            act,
            config,
        )

    # --------------------------------
    # User asks about the restaurant
    # --------------------------------

    if act == "request":
        return handle_restaurant_request(
            state,
            text,
        )

    # --------------------------------
    # User accepts the offer
    # --------------------------------

    if act == "affirm" or text in {
        "yes",
        "y",
        "yeah",
        "sure",
        "okay",
        "ok",
        "change",
    }:
        state.state = DialogStateName.COLLECT_PREFERENCES

        system_response = response(
            "ask_preference_change"
        )

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # User declines
    # --------------------------------

    if act in {"deny", "negate"} or text in {
        "no",
        "n",
        "nope",
    }:
        state.state = DialogStateName.END

        system_response = response("goodbye")

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # End conversation
    # --------------------------------

    if act in {"bye", "thankyou"} or text in {
        "bye",
        "goodbye",
        "thanks",
        "thank you",
        "thankyou",
    }:
        state.state = DialogStateName.END

        system_response = response("goodbye")

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # Repeat
    # --------------------------------

    if act == "repeat":
        return state, state.last_response

    # --------------------------------
    # Otherwise
    # --------------------------------

    system_response = response(
        "offer_preference_change"
    )

    state.last_response = system_response

    return state, system_response

def transition(
    state: DialogState,
    user_input: UserInput,
    config,
):
    act = user_input.dialog_act.lower()
    text = user_input.text

    # ------------------------------------
    # Global transitions
    # ------------------------------------
    if act in {"bye", "thankyou"} or text in {
            "bye",
            "goodbye",
            "thanks",
            "thank you",
            "thankyou",
        }: # TODO: check with TA if we call use text fallback, because bye is not classified correctly

        state.state = DialogStateName.END

        system_response = response("goodbye")

        state.last_response = system_response

        return state, system_response

    if act == "restart":

        new_state = DialogState(
            state=DialogStateName.WELCOME
        )

        system_response = response("welcome")

        new_state.last_response = system_response

        return new_state, system_response

    if act == "repeat":

        return state, state.last_response

    # ------------------------------------
    # State-specific transitions
    # ------------------------------------

    if state.state == DialogStateName.WELCOME:
        return handle_welcome(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.COLLECT_PREFERENCES:
        return handle_preferences(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.CONFIRM_SLOT:
        return handle_confirmation(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.ADDITIONAL_REQUIREMENT:
        return handle_additional_requirements(state, text, act, config)

    if state.state == DialogStateName.LOOKUP:
        return handle_lookup(
            state,
            config,
        )

    if state.state == DialogStateName.RECOMMEND:
        # User wants to change preferences
        if act == "inform":
            return handle_preferences(
                state,
                text,
                act,
                config,
            )
        if act == "request":
            return handle_restaurant_request(
                state,
                text,
            )
        if act == "confirm":
            return handle_restaurant_confirmation(state, text, config)

        if act == "reqmore":
            return handle_offer_preference_change(state, text, act, config)

        return handle_recommendation(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.ALTERNATIVE:
        # User wants to change preferences
        if act == "inform":
            return handle_preferences(
                state,
                text,
                act,
                config,
            )
        if act == "request":
            return handle_restaurant_request(
                state,
                text,
            )
        if act == "confirm":
            return handle_restaurant_confirmation(state, text, config)
        return handle_alternative(
            state,
            act,
            config,
        )

    if state.state == DialogStateName.NO_MATCH:
        return handle_no_match(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.OFFER_PREFERENCE_CHANGE:
        return handle_offer_preference_change(
            state,
            text,
            act,
            config,
        )

    if state.state == DialogStateName.END:
        return state, response("ended")

    raise ValueError(
        f"Unknown dialog state: {state.state}"
    )
