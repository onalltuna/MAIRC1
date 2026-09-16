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


def train_classifier(classifier):
    classifier = classifiers[classifier]
    print(f"\nyou are training the {classifier} model")
    classifier.train()


def test_classifier(classifier):
    classifier = classifiers[classifier]
    print(f"\nYou are testing the {classifier} model")
    classifier.test()


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

    test_parser = subparsers.add_parser("test", help="Test a classifier")

    test_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )

    dialog_parser = subparsers.add_parser("dialog", help="Start the restaurant dialog system")

    dialog_parser.add_argument(
        "--classifier",
        choices=classifiers.keys(),
        required=True,
    )

    manual_parser = subparsers.add_parser("manual", help="Manual utterance classifier")
    manual_parser.add_argument("--classifier", choices=classifiers.keys(),required=True)

    args = parser.parse_args()

    if args.command == "train":
        train_classifier(args.classifier)

    elif args.command == "test":
        test_classifier(args.classifier)

    elif args.command == "dialog":
        activate_dialog_with_classifer(args.classifier)

    elif args.command == "manual":
        activate_manual_classifier(args.classifier)


if __name__ == "__main__":
    main()
