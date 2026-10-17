import classifiers.ml_classifier_1 as ml1

from dialog.state import DialogState, DialogConfig, UserInput, DialogStateName
from dialog.transition import transition
from dialog.responses import response
from dialog.tts import speak
from dialog.logging_test import start_log, log_user, log_system, end_log


def system_say(text, use_tts):
    print(f"\nS: {text}")
    if use_tts:
        speak(text)


class DialogSession:
    """
    Manages a single dialog conversation.

    This class supports both a graphical UI and other interfaces
    by processing one user message at a time.
    """

    def __init__(
        self,
        is_grouped,
        use_bert,
        slot_fallback="levenshtein",
        reasoning_transparency=True,
        tts=False,
        user_name="User",
    ):
        self.is_grouped = is_grouped
        self.use_bert = use_bert
        self.tts = tts

        self.config = DialogConfig(
            slot_fallback=slot_fallback,
            reasoning_transparency=reasoning_transparency,
        )

        self.state = DialogState()
        self.log_file = start_log(
            user_name=user_name,
            reasoning_transparency=reasoning_transparency,
        )
        self.finished = False

        # Initial system utterance
        self.welcome_response = response("welcome")
        self.state.last_response = self.welcome_response

        log_system(
            self.log_file,
            self.welcome_response,
            state=self.state.state,
        )

    def process_message(self, utterance):
        """
        Process one user message and return the system response.

        Returns:
            tuple[str | None, bool]:
                The system response, if any, and whether the
                conversation has finished.
        """

        utterance = utterance.strip()

        if not utterance or self.finished:
            return None, self.finished

        if utterance == "/exit":
            self.close()
            return "Goodbye!", True

        # Classify the user's utterance.
        pred = ml1.predict(
            utterance=utterance,
            isGrouped=self.is_grouped,
            use_bert=self.use_bert,
        )

        # Log the user's message.
        log_user(
            self.log_file,
            utterance,
            dialog_act=pred,
            state=self.state.state,
        )

        # Apply the existing dialog transition logic.
        self.state, system_response = transition(
            self.state,
            UserInput(
                text=utterance,
                dialog_act=pred,
            ),
            self.config,
        )

        # Log the system's response.
        if system_response:
            log_system(
                self.log_file,
                system_response,
                state=self.state.state,
            )

            if self.tts:
                speak(system_response)

        # End the conversation if the state machine reaches END.
        if self.state.state == DialogStateName.END:
            self.close()

        return system_response, self.finished

    def close(self):
        """Close the conversation and finish its log."""
        if not self.finished:
            self.finished = True
            end_log(self.log_file)


def manage(
    is_grouped,
    use_bert,
    slot_fallback="levenshtein",
    reasoning_transparency=True,
    tts=False,
):
    """
    Run the dialog manager through the terminal.
    """

    session = DialogSession(
        is_grouped=is_grouped,
        use_bert=use_bert,
        slot_fallback=slot_fallback,
        reasoning_transparency=reasoning_transparency,
        tts=tts,
    )

    system_say(session.welcome_response, use_tts=tts)

    try:
        while not session.finished:
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

            system_response, _ = session.process_message(utterance)

            if system_response:
                system_say(system_response, use_tts=tts)

    finally:
        session.close()