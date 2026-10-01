import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
from dialog.state import DialogState, DialogConfig, UserInput
from dialog.transition import transition
from dialog.slot_extractor import extract_slots

#responses templates from response_generator
from dialog.response_generator import responses

#for the repeat response, we need to keep track of what has been said previously
#last_response = None

classifiers = {
    "rulebased": rb,
    "ml1": ml1,
    "ml2": ml2,
}


def manage(
    is_grouped,
    use_bert,
    slot_fallback="levenshtein",
):

    config = DialogConfig(
        slot_fallback=slot_fallback,
        reasoning_transparency=True,
    )

    state = DialogState()

    print("Welcome to the restaurant dialog system.")

    while state.state != "END":

        utterance = input("> ").strip()

        if not utterance:
            continue

        if utterance == "exit":
            print("Exiting dialog manager")
            break

        # -----------------------------
        # 1. Classify
        # -----------------------------

        pred = ml1.predict(
            utterance=utterance,
            isGrouped=is_grouped,
            use_bert=use_bert,
        )

        # -----------------------------
        # 2. Transition
        # -----------------------------

        state, response = transition(
            state,
            UserInput(
                text=utterance,
                dialog_act=pred,
            ),
            config,
        )

        # -----------------------------
        # 3. Respond
        # -----------------------------

        if response:
            print(response)