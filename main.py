import argparse
import sys
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
import dialog.dialog_manager as dm

classifiers = {
    "rulebased": rb,
    "ml1": ml1,
    "ml2": ml2,
}


def train_classifier(classifier_name, isGrouped, use_bert):
    classifier = classifiers[classifier_name]
    try:
        classifier.train(isGrouped=isGrouped, use_bert=use_bert)
    except FileNotFoundError as e:
        print(f"Error: could not find a required file while training '{classifier_name}': {e.filename}")
        print("Make sure you've run data_preprocess.py to generate the processed data files.")
        sys.exit(1)



def test_classifier(classifier_name, isHeldOut, isGrouped, use_bert):
    classifier = classifiers[classifier_name]
    print(f"\nYou are testing the {classifier_name} model with the following settings: grouped={isGrouped}, bert={use_bert}\n")
    try:
        classifier.test(isHeldOut=isHeldOut, isGrouped=isGrouped, use_bert=use_bert)
    except FileNotFoundError as e:
        print(f"Error: could not find a required file while testing '{classifier_name}': {e.filename}")
        if isHeldOut:
            print("Make sure the held-out file exists at data/raw/dialog_acts_test.dat")
        else:
            print("Make sure you've trained this classifier first, e.g.:")
            print(f"  python main.py train --classifier {classifier_name} --grouped {'y' if isGrouped else 'n'}"
                  f"{' --bert y' if use_bert else ''}")
        sys.exit(1)


def activate_dialog_with_classifier(classifier, is_grouped, use_bert):

    dm.manage(classifier, is_grouped, use_bert)


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

    dialog_parser = subparsers.add_parser("dialog", help="Start the restaurant dialog system")
    dialog_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )
    dialog_parser.add_argument("--grouped", choices=["y", "n"], required=True)
    dialog_parser.add_argument("--bert", choices=["y", "n"], required=False, default="n")

    heldout_parser = subparsers.add_parser("heldout", help="Held-out test set")
    heldout_parser.add_argument("--classifier", choices=classifiers.keys(), required=True)
    heldout_parser.add_argument("--grouped",choices=["y", "n"], required=True)
    heldout_parser.add_argument("--bert",choices=["y", "n"], required=True)

    args = parser.parse_args()
    is_grouped = args.grouped == "y"
    use_bert = args.bert == "y"

    if args.command == "train":
        train_classifier(args.classifier, is_grouped, use_bert)
    elif args.command == "test":
        test_classifier(args.classifier, isHeldOut=False, isGrouped=is_grouped, use_bert=use_bert)
    elif args.command == "dialog":
        activate_dialog_with_classifier(args.classifier, is_grouped, use_bert)
    elif args.command == "heldout":
        test_classifier(args.classifier, isHeldOut=True, isGrouped=is_grouped, use_bert=use_bert)


if __name__ == "__main__":
    main()
