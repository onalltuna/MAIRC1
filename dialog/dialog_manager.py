import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
from dialog.state import DialogState, DialogConfig, UserInput, DialogStateName
from dialog.transition import transition
from dialog.responses import response


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

    # Initial system utterance
    welcome_response = response("welcome")
    state.last_response = welcome_response
    print(welcome_response)

    while state.state != DialogStateName.END:

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

        state, system_response = transition(
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

        if system_response:
            print(system_response)