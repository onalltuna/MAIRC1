import classifiers.ml_classifier_1 as ml1
from dialog.state import DialogState, DialogConfig, UserInput, DialogStateName
from dialog.transition import transition
from dialog.responses import response


def manage(
    is_grouped,
    use_bert,
    slot_fallback="levenshtein",
    reasoning_transparency=True,
):

    config = DialogConfig(
        slot_fallback=slot_fallback,
        reasoning_transparency=reasoning_transparency,
    )

    state = DialogState()

    # Initial system utterance
    welcome_response = response("welcome")
    state.last_response = welcome_response
    print(f"\n{welcome_response}")

    while state.state != DialogStateName.END:

        utterance = input("> ").strip()

        if not utterance:
            continue

        if utterance == "/exit":
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

        # print(f"prediction: {pred}")

        # -----------------------------
        # 2. Transition
        # -----------------------------

        # print(f"\nprevious_state: {state}")
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
            print(f"\n{system_response}")