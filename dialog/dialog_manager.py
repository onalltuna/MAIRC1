import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
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


def manage(classifier_name, is_grouped, use_bert, slot_fallback="levenshtein"):
    classifier = classifiers[classifier_name]

    print(
        f"\nWelcome to dialog manager! "
        f"You are using the {classifier.name} classifier."
    )
    print(
        f"Slot extraction fallback: {slot_fallback}"
    )
    print("Type an utterance. Type /exit or press Ctrl+C to exit.\n")
    state = {
        "food": None,
        "price": None,
        "area": None,
    }
    # Non-exact matches which need confirmation
    pending_confirmations = []

    while True:
        try:
            utterance = input("> ").strip().lower()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting dialog manager")
            break

        if not utterance:
            continue

        if utterance == "/exit":
            print("Exiting dialog manager")
            break

        if pending_confirmations:
            result = pending_confirmations[0]
            if utterance in {"yes", "y", "yeah", "yep", "correct"}:
                pending_confirmations.pop(0)
                state[result.slot] = result.value
                print(f"Confirmed: {result.slot} = {result.value}")
            elif utterance in {"no", "n", "nope", "wrong"}:
                pending_confirmations.pop(0)
                print("Okay, I won't use that value.")
            else:
                print("Please answer yes or no.")
                continue
            if pending_confirmations:
                next_result = pending_confirmations[0]
                print(f"Did you mean '{next_result.value}' for {next_result.slot}? (yes/no)")
            else:
                print("All pending confirmations handled.")
                print(f"Current state: {state}")

            continue

        try:
            if classifier_name == "rulebased":
                pred = rb.predict(utterance)
            elif classifier_name == "ml1":
                pred = ml1.predict(
                    utterance=utterance,
                    isGrouped=is_grouped,
                    use_bert=use_bert,
                )
            else:
                pred = ml2.predict(
                    utterance=utterance,
                    isGrouped=is_grouped,
                    use_bert=use_bert,
                )

        except FileNotFoundError as e:
            print(f"\nError: could not find a required model file: '{e.filename}'.")
            print("Make sure you've trained this classifier configuration first, e.g.:")
            print(f"  python main.py train --classifier {classifier_name} --grouped {'y' if is_grouped else 'n'}"
                  f"{' --bert y' if use_bert else ''}")
            break

        print(f"Predicted dialog act: {pred}")

        #if the user asks to repeat, repeat previous answer, or the welcome message -? not sure anymore if this is needed
       # if pred.lower() == "repeat":
       #     previous = last_response or responses["welcome"]
        #    print(responses["repeat_re"].format(last_response=previous))
        #    print()
         #   continue


        # Only extract slots from INFORM utterances.
        if pred.lower() == "inform":
            results = extract_slots(utterance, fallback=slot_fallback)

            if results:
                print("\nExtracted slots:")
                for result in results:
                    print(f"  {result.slot}: {result.value} ({result.method})")
                    if result.needs_confirmation:
                        pending_confirmations.append(result)
                        print(f"  -> confirmation required for {result.original_value}.")
                    else:
                        state[result.slot] = result.value
                if pending_confirmations:
                    result = pending_confirmations[0]
                    print(f"Did you mean '{result.value}' for {result.slot}? (yes/no)")
            else:
                print("\nNo slots extracted.")
        print()