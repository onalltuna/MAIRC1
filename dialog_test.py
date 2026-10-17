import os
import sys

from dialog.dialog_ui import launch_dialog_ui


# The dialog system always uses the MLP classifier
# trained on the grouped split with DistilBERT embeddings.
DIALOG_IS_GROUPED = True
DIALOG_USE_BERT = True

DIALOG_RESTAURANT_DB = "dialog/restaurant_info_extended.csv"


def main():
    if not os.path.exists(DIALOG_RESTAURANT_DB):
        print(
            "Error: Restaurant database not found:\n"
            f"  {DIALOG_RESTAURANT_DB}\n"
            "Run this script from the project root directory."
        )
        sys.exit(1)

    launch_dialog_ui(
        is_grouped=DIALOG_IS_GROUPED,
        use_bert=DIALOG_USE_BERT,
        slot_fallback="levenshtein",
    )


if __name__ == "__main__":
    main()