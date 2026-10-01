import random
from dataclasses import dataclass

from dialog.slot_extractor import extract_slots
from dialog.responses import response
from dialog.state import DialogState, DialogStateName
from dialog.restaurant_lookup import find_restaurants


@dataclass
class UserInput:
    text: str
    dialog_act: str


def handle_welcome(
    state,
    text,
    act,
    config,
):
    """
    Handle the first user turn in the dialogue.
    """

    if act == "inform":
        return handle_preferences(
            state,
            text,
            act,
            config,
        )

    if act == "request":
        system_response = response("welcome")

        state.state = DialogStateName.COLLECT_PREFERENCES
        state.last_response = system_response

        return state, system_response

    system_response = response("welcome")

    state.state = DialogStateName.COLLECT_PREFERENCES
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

    if state.price is None:
        return response("askpricerange")

    if state.area is None:
        return response("askarea")

    return ""


def handle_preferences(
    state,
    text,
    act,
    config,
):
    if act != "inform":
        system_response = response("askfood")

        state.last_response = system_response

        return state, system_response

    results = extract_slots(
        text,
        fallback=config.slot_fallback,
    )

    for result in results:

        if result.needs_confirmation:
            state.pending_confirmations.append(result)

        else:
            setattr(
                state,
                result.slot,
                result.value,
            )

    # --------------------------------
    # Need confirmation?
    # --------------------------------

    if state.pending_confirmations:

        state.state = DialogStateName.CONFIRM_SLOT

        result = state.pending_confirmations[0]

        system_response = generate_confirmation(result)

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # Check whether all preferences
    # are known
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
    # Ask for missing preference
    # --------------------------------

    system_response = ask_for_missing_slot(state)

    state.state = DialogStateName.COLLECT_PREFERENCES
    state.last_response = system_response

    return state, system_response


def generate_confirmation(result):
    """
    Generate a confirmation response for an approximate
    slot match.
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

        return state, ask_for_missing_slot(state)

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

        setattr(
            state,
            result.slot,
            result.value,
        )

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

        system_response = generate_confirmation(next_result)

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # All confirmations finished
    # --------------------------------

    state.state = DialogStateName.COLLECT_PREFERENCES

    return transition(
        state,
        UserInput(
            text="",
            dialog_act="internal_continue",
        ),
        config,
    )


def handle_lookup(state, config):

    matches = find_restaurants(
        food=state.food,
        price=state.price,
        area=state.area,
    )

    # --------------------------------
    # No matches
    # --------------------------------

    if not matches:

        state.state = DialogStateName.NO_MATCH

        system_response = response("nomatch")

        state.last_response = system_response

        return state, system_response

    # --------------------------------
    # Randomly choose one restaurant
    # --------------------------------

    selected = random.choice(matches)

    state.current_restaurant = selected

    # Store the other matching restaurants
    state.alternatives = [
        restaurant
        for restaurant in matches
        if restaurant != selected
    ]

    state.state = DialogStateName.RECOMMEND

    return transition(
        state,
        UserInput(
            text="",
            dialog_act="internal_recommend",
        ),
        config,
    )


def generate_recommendation(restaurant):
    """
    Generate the recommendation using a response template.
    """

    if restaurant is None:
        return response("nomatch")

    return response(
        "recommend",
        restaurantname=restaurant["restaurantname"],
        food=restaurant["food"],
        area=restaurant["area"],
        pricerange=restaurant["pricerange"],
    )

def handle_restaurant_request(state, config):

    restaurant = state.current_restaurant

    if restaurant is None:
        system_response = response("nomatch")
        state.last_response = system_response
        return state, system_response

    system_response = response(
        "postcode",
        postcode=restaurant["postcode"],
    )

    state.last_response = system_response

    return state, system_response

def handle_recommendation(state, act, config):

    if act in {"reqalts", "alternative"}:
        state.state = DialogStateName.ALTERNATIVE

        return handle_alternative(
            state,
            act,
            config,
        )

    if act == "request":
        return handle_restaurant_request(
            state,
            config,
        )

    system_response = generate_recommendation(
        state.current_restaurant
    )

    state.last_response = system_response

    return state, system_response

def handle_alternative(state, act, config):
    """
    Handle a request for an alternative restaurant.

    Uses the restaurants already found for the current
    set of preferences.
    """

    if not state.alternatives:
        system_response = response("noalternative")

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

    if act == "inform":
        # The user is providing a new or changed preference.
        return handle_preferences(
            state,
            text,
            act,
            config,
        )

    system_response = response("nomatch")

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

    if act == "restart":

        new_state = DialogState(
            state=DialogStateName.WELCOME
        )

        system_response = response("restart")

        new_state.last_response = system_response

        return new_state, system_response

    if act == "repeat":

        return state, state.last_response

    if act == "bye":

        state.state = DialogStateName.END

        system_response = response("goodbye")

        state.last_response = system_response

        return state, system_response

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

    if state.state == DialogStateName.LOOKUP:
        return handle_lookup(
            state,
            config,
        )

    if state.state == DialogStateName.RECOMMEND:
        return handle_recommendation(
            state,
            act,
            config,
        )

    if state.state == DialogStateName.ALTERNATIVE:
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

    if state.state == DialogStateName.END:
        return state, response("ended")

    raise ValueError(
        f"Unknown dialog state: {state.state}"
    )