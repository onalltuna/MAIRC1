import classifiers.ml_classifier_1 as ml1
from dialog.state import DialogState, DialogConfig, UserInput, DialogStateName
from dialog.transition import transition
from dialog.responses import response
from dialog.tts import speak
from dialog.logging import start_log, log_user, log_system, end_log

def system_say(text, use_tts):
    print(f"\nS: {text}")
    if use_tts:
        speak(text)
def manage(
    is_grouped,
    use_bert,
    slot_fallback="levenshtein",
    reasoning_transparency=True,
    tts = False
):

    config = DialogConfig(
        slot_fallback=slot_fallback,
        reasoning_transparency=reasoning_transparency,
    )

    state = DialogState()
    log_file = start_log()
    # Initial system utterance
    welcome_response = response("welcome")
    state.last_response = welcome_response
    system_say(welcome_response,use_tts=tts)
    log_system(log_file, welcome_response, state=state.state)

    while state.state != DialogStateName.END:

        try:
            utterance = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting dialog manager")
            break

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

        # -----------------------------
        # 2. Transition
        # -----------------------------
        log_user(log_file, utterance, dialog_act=pred, state=state.state)
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
            log_system(log_file, system_response, state=state.state)
            system_say(system_response,use_tts=tts)

    end_log(log_file)