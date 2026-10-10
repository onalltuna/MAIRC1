import random
from dataclasses import dataclass
from dialog.slot_extractor import extract_slots, extract_candidates
from dialog.responses import response
from dialog.state import DialogState, DialogStateName, UserInput
from dialog.restaurant_lookup import find_restaurants
from dialog.reasoning import derive_properties, parse_additional_requirement, apply_rules, describe_property
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

FAREWELL_PHRASES = {"bye", "goodbye", "thanks", "thank you", "thankyou"}


NEG = re.compile(r"\b(not|don'?t|dont|do not|no)\b")


def is_farewell(normalized_text: str) -> bool:
    for phrase in FAREWELL_PHRASES:
        if re.search(r"\b" + re.escape(phrase) + r"\b", normalized_text):
            return True
    return False


def is_polite_decline(normalized_text: str) -> bool:
    # "no thanks" / "no, thank you" answers a yes/no question — it is not
    # a farewell unless the user also says bye
    if re.search(r"\b(bye|goodbye)\b", normalized_text):
        return False
    return re.match(r"^(no|nope|nah)\b[\s,]*(thanks|thank you|thankyou)\b", normalized_text) is not None


# states where the system just asked a yes/no question, so "no thanks"
# is an answer rather than the end of the conversation
YES_NO_QUESTION_STATES = {
    DialogStateName.ADDITIONAL_REQUIREMENT,
    DialogStateName.CONFIRM_SLOT,
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





def handle_nothing_new(state, text, act):
    if act == "request":
        return handle_restaurant_request(state, text)
    if state.current_restaurant and (act in {"negate", "deny"}):
        state.state = DialogStateName.OFFER_DETAILS
        resp = response("nothing_to_change", restaurantname=state.current_restaurant["restaurantname"])
    else:
        resp = response("ask_preference_change")
    state.last_response = resp
    return state, resp






def handle_restaurant_confirmation(state, text, config):
    restaurant = state.current_restaurant

    if restaurant is None:
        system_response = response("nomatch", food=state.food, area=state.area, pricerange=state.price)
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

    if act in {"negate", "deny"} or normalized in no_requirement or is_polite_decline(normalized):
        state.additional_requirement = None
    else:
        prop, desired = parse_additional_requirement(text)
        state.additional_requirement = {"property": prop, "value": desired} if prop else None

    state.additional_requirement_asked = True
    state.state = DialogStateName.LOOKUP
    return transition(state, UserInput(text="", dialog_act="internal_lookup"), config)


def handle_welcome(state, text, act, config):
    #issue was that if you say 'hello, i want x', it will aks again for your prefertence even if you just gave the preference. 
    # hope this will fix it by first checking if any slots can be filled, and then go to the inform act
    results = extract_slots(text, fallback=config.slot_fallback,
                            expected_slot=get_missing_slot(state))
    # a greeting like "hi" should not be fuzzy-matched to a food ("thai");
    # only trust exact keyword matches when the user is saying hello
    if act == "hello":
        results = [r for r in results if r.method == "keyword"]
    if results:
        return handle_preferences(state, text, "inform", config)

    # the user named a preference we couldn't match (e.g. "Swedish food") —
    # let handle_preferences say it is unrecognized instead of asking again
    if act == "inform" and extract_candidates(text):
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
    state.shown.clear()


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

    if act != "inform" and not results and not is_no_preference(normalized_text):
        if all_preferences_known(state): #
            return handle_nothing_new(state, text, act)
        system_response = ask_for_missing_slot(state)
        state.last_response = system_response
        return state, system_response

    if not results and is_no_preference(normalized_text):
        if missing_slot is not None:
            setattr(state, missing_slot, "any")
            if all_preferences_known(state):
                if not state.additional_requirement_asked and has_multiple_matches(state):
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
        if not state.additional_requirement_asked and has_multiple_matches(state):
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

    elif act in {"deny", "negate"} or text in {"no", "n", "nope", "wrong"} or is_polite_decline(text.lower().strip()):
        rejected = state.pending_confirmations.pop(0)

        missing_slot = get_missing_slot(state)
        extracted = extract_slots(
            text,
            fallback=config.slot_fallback,
            expected_slot=missing_slot,
            exclude_value=rejected.value,   # see note below
        )
        for result in extracted:
            if result.slot == rejected.slot and result.value != rejected.value:
                setattr(state, result.slot, result.value)
                reset_restaurant_results(state)
                break

    # --------------------------------
    # Unknown confirmation response
    # --------------------------------

    else:
        extracted = extract_slots(text, fallback=config.slot_fallback)
        exact = [r for r in extracted if r.method == "keyword"]
        if exact:
            filled = {r.slot for r in exact}
            state.pending_confirmations = [
                p for p in state.pending_confirmations if p.slot not in filled
            ]
            return handle_preferences(state, text, "inform", config)

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
            derived = derive_properties(r)
            if prop in derived and derived[prop][0] == desired:
                r = dict(r)
                r["_reasoning_property"] = prop
                r["_reasoning_value"] = derived[prop][0]
                r["_reasoning_explanation"] = derived[prop][1]
                r["_reasoning_contradiction"] = derived[prop][2]
                filtered.append(r)

        if matches and not filtered:
            state.state = DialogStateName.NO_MATCH
            system_response = response("nomatch_requirement", requirement=describe_property(prop, desired))
            state.last_response = system_response
            return state, system_response

        matches = filtered

    blocked = state.shown | state.rejected
    matches = [r for r in matches if r["restaurantname"] not in blocked]

    if not matches:
        if blocked:
            state.state = DialogStateName.OFFER_PREFERENCE_CHANGE
            system_response = response("offer_preference_change")
        else:
            state.state = DialogStateName.NO_MATCH
            system_response = response("nomatch", food=state.food, area=state.area, pricerange=state.price)
        state.last_response = system_response
        return state, system_response

    selected = random.choice(matches)
    state.shown.add(selected["restaurantname"])
    state.current_restaurant = selected
    state.alternatives = [r for r in matches if r != selected]
    state.state = DialogStateName.RECOMMEND
    return transition(state, UserInput(text="", dialog_act="internal_recommend"), config)


def generate_recommendation(restaurant, show_reasoning=True):
    if restaurant is None:
        return response("nomatchfound")

    base = response(
        "recommend",
        restaurantname=restaurant["restaurantname"],
        food=restaurant["food"],
        area=restaurant["area"],
        pricerange=restaurant["pricerange"],
    )

    if show_reasoning:
        base += generate_reasoning(restaurant)

    return base


def generate_reasoning(restaurant):
    """
    Explain why the restaurant satisfies the additional requirement,
    including how a contradiction between rules was resolved.
    """
    explanation = restaurant.get("_reasoning_explanation")
    if not explanation:
        return ""

    phrase = describe_property(restaurant["_reasoning_property"], restaurant["_reasoning_value"])
    text = f" It {phrase} because {explanation}."

    note = restaurant.get("_reasoning_contradiction")
    if note:
        text += (
            f" Another rule suggests otherwise ({note}), "
            f"but I gave priority to the rule in favour."
        )

    return text




def handle_offer_details(state, text, act, config):
    if act == "affirm":
        return handle_restaurant_request(state, "address phone postcode")
    if act in {"negate", "deny"}:
        state.state = DialogStateName.RECOMMEND
        resp = response("anything_else")
        state.last_response = resp
        return state, resp
    if act == "request":
        return handle_restaurant_request(state, text)
    if act == "inform":
        return handle_preferences(state, text, act, config)
    resp = response("restaurant_info", restaurantname=state.current_restaurant["restaurantname"])
    state.last_response = resp
    return state, resp







def handle_restaurant_request(state, text):
    restaurant = state.current_restaurant

    if restaurant is None:
        system_response = response("nomatch", food=state.food, area=state.area, pricerange=state.price)
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
        state.state = DialogStateName.OFFER_DETAILS
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

    if act in {"bye", "thankyou"} or is_farewell(text.lower().strip()):
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
        food = alternative["food"],
        area = alternative["area"],
        pricerange = alternative["pricerange"]
    )

    if config.reasoning_transparency:
        system_response += generate_reasoning(alternative)

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

    system_response = response("nomatch", food=state.food, area=state.area, pricerange=state.price)

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

    if act in {"bye", "thankyou"} or is_farewell(text.lower().strip()):
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
    normalized_text = text.lower().strip()
    declines_question = (
        state.state in YES_NO_QUESTION_STATES
        and is_polite_decline(normalized_text)
    )

    if (act in {"bye", "thankyou"} or is_farewell(normalized_text)) and not declines_question:
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


        
    if state.state in {DialogStateName.RECOMMEND, DialogStateName.ALTERNATIVE} and state.current_restaurant:
         name = state.current_restaurant["restaurantname"]
         if name.lower() in text.lower() and NEG.search(text.lower()):
            state.rejected.add(name)
            state.alternatives = [a for a in state.alternatives if a["restaurantname"] not in state.rejected]
            state, nxt = handle_alternative(state, "reqalts", config)
            state.last_response = f"Okay, I won't suggest {name} again. {nxt}"
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

    if state.state == DialogStateName.OFFER_DETAILS:
        return handle_offer_details(state, text, act, config)

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
