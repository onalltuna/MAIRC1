import argparse
import sys
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
import dialog.dialog_manager as dm
import prompt as prompt

classifiers = {
    "rulebased": rb,
    "ml1": ml1,
    "ml2": ml2,
}


def train_classifier(classifier_name, isGrouped, use_bert):
    classifier = classifiers[classifier_name]
    print(f"\nYou are training the {classifier.name} model with the following settings: grouped={isGrouped}, bert={use_bert}\n")
    try:
        classifier.train(isGrouped=isGrouped, use_bert=use_bert)
    except FileNotFoundError as e:
        print(f"Error: could not find a required file while training '{classifier_name}': {e.filename}")
        print("Make sure you've run data_preprocess.py to generate the processed data files first:")
        print("  python data_preprocess.py")
        sys.exit(0)



def test_classifier(classifier_name, isHeldOut, isGrouped, use_bert):
    classifier = classifiers[classifier_name]
    print(f"\nYou are testing the {classifier.name} model with the following settings: grouped={isGrouped}, bert={use_bert}, held-out:{isHeldOut}\n")
    try:
        classifier.test(isHeldOut=isHeldOut, isGrouped=isGrouped, use_bert=use_bert)
    except FileNotFoundError as e:
        print(f"Error: could not find the required file while testing '{classifier_name}': {e.filename}")
        if isHeldOut:
            print("\nMake sure the held-out file exists at data/raw/dialog_acts_test.dat")
        else:
            print("\nMake sure you've run the preprocessing script and trained this classifier first, e.g.:")
            print("  python data_preprocess.py")
            print(f"  python main.py train --classifier {classifier_name} --grouped {'y' if isGrouped else 'n'}"
                  f"{' --bert y' if use_bert else ''}")
        sys.exit(0)


def activate_prompt_with_classifier(classifier_name, is_grouped, use_bert):
    try:
        prompt.manage(classifier_name, is_grouped, use_bert)
    except FileNotFoundError as e:
        print(f"Error: could not find a required model file: '{e.filename}'.")
        print("Make sure you've trained this classifier configuration first, e.g.:")
        print(f"  python main.py train --classifier {classifier_name} --grouped {'y' if is_grouped else 'n'}"
              f"{' --bert y' if use_bert else ''}")
        sys.exit(1)


def activate_dialog_with_classifier(classifier_name, is_grouped, use_bert, slot_fallback):
    try:
        dm.manage(classifier_name, is_grouped, use_bert, slot_fallback)
    except FileNotFoundError as e:
        print(f"Error: could not find a required model file: '{e.filename}'.")
        print("Make sure you've trained this classifier configuration first.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Restaurant dialog system")

    subparsers = parser.add_subparsers(dest="command", required=True)

    train_parser = subparsers.add_parser("train", help="Train a classifier")
    train_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )
    train_parser.add_argument("--grouped", choices=["y", "n"], required=True)
    train_parser.add_argument("--bert", choices=["y", "n"], required=False, default="n")


    test_parser = subparsers.add_parser("test", help="Test a classifier")
    test_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )
    test_parser.add_argument("--grouped", choices=["y", "n"], required=True)
    test_parser.add_argument("--bert", choices=["y", "n"], required=False, default="n")

    prompt_parser = subparsers.add_parser("prompt", help="Start the prompt based classification system")
    prompt_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )
    prompt_parser.add_argument("--grouped", choices=["y", "n"], required=True)
    prompt_parser.add_argument("--bert", choices=["y", "n"], required=False, default="n")


    dialog_parser = subparsers.add_parser("dialog", help="Start the restaurant dialog system")
    dialog_parser.add_argument("--classifier",choices=classifiers.keys(),required=True)
    dialog_parser.add_argument("--grouped", choices=["y", "n"], required=True)
    dialog_parser.add_argument("--bert", choices=["y", "n"], required=False, default="n")
    dialog_parser.add_argument(
        "--slot-fallback",
        choices=["levenshtein", "semantic"],
        default="levenshtein",
        help="Slot extraction fallback method"
    )

    heldout_parser = subparsers.add_parser("heldout", help="Held-out test set")
    heldout_parser.add_argument("--classifier", choices=classifiers.keys(), required=True)
    heldout_parser.add_argument("--grouped",choices=["y", "n"], required=True)
    heldout_parser.add_argument("--bert",choices=["y", "n"], required=False, default="n")

    args = parser.parse_args()
    is_grouped = args.grouped == "y"
    use_bert = args.bert == "y"

    if args.command == "train":
        train_classifier(args.classifier, is_grouped, use_bert)
    elif args.command == "test":
        test_classifier(args.classifier, isHeldOut=False, isGrouped=is_grouped, use_bert=use_bert)
    elif args.command == "prompt":
        activate_prompt_with_classifier(args.classifier, is_grouped, use_bert)
    elif args.command == "dialog":
        activate_dialog_with_classifier(args.classifier, is_grouped, use_bert, args.slot_fallback)
    elif args.command == "heldout":
        test_classifier(args.classifier, isHeldOut=True, isGrouped=is_grouped, use_bert=use_bert)


if __name__ == "__main__":
    main()
