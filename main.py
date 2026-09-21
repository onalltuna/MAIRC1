import argparse
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2
import dialog.dialog_manager as dm

classifiers = {
    "rulebased": rb,
    "ml1": ml1,
    "ml2": ml2,
}


def train_classifier(classifier,isGrouped):
    classifier = classifiers[classifier]
    classifier.train(isGrouped)


def test_classifier(classifier, isHeldOut, isGrouped):
    classifier = classifiers[classifier]
    print(f"\nYou are testing the {classifier} model with {isGrouped} setting")
    classifier.test(isHeldOut=isHeldOut, isGrouped=isGrouped)


def activate_dialog_with_classifer(classifier):

    dm.manage(classifier)


def activate_manual_classifier(classifier):
#TODO logic for manual classification should be implemented here
    print(f"manual classifier is activated with: {classifier}")


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


    test_parser = subparsers.add_parser("test", help="Test a classifier")

    test_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )

    test_parser.add_argument("--grouped", choices=["y", "n"], required=True)

    dialog_parser = subparsers.add_parser("dialog", help="Start the restaurant dialog system")

    dialog_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )

    manual_parser = subparsers.add_parser("manual", help="Manual utterance classifier")
    manual_parser.add_argument("--classifier", choices=classifiers.keys(),required=True)

    heldout_parser = subparsers.add_parser("heldout", help="Held-out test set")
    heldout_parser.add_argument("--classifier", choices=classifiers.keys(), required=True)

    args = parser.parse_args()

    if args.command == "train":
        if args.grouped == "y":
            train_classifier(args.classifier,isGrouped=True)
        else:
            train_classifier(args.classifier,isGrouped=False)

    elif args.command == "test":
        if args.grouped == "y":
            test_classifier(args.classifier, isHeldOut=False, isGrouped=True)
        else:
            test_classifier(args.classifier, isHeldOut=False, isGrouped=False)
    elif args.command == "dialog":
        activate_dialog_with_classifer(args.classifier)

    elif args.command == "manual":
        activate_manual_classifier(args.classifier)

    elif args.command == "heldout":
        test_classifier(args.classifier, isHeldOut=True, isGrouped=False)


if __name__ == "__main__":
    main()
