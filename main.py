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


def train_classifier(classifier,isGrouped, use_bert):
    classifier = classifiers[classifier]
    classifier.train(isGrouped, use_bert=use_bert)


def test_classifier(classifier, isHeldOut, isGrouped, use_bert):
    classifier = classifiers[classifier]
    print(f"\nYou are testing the {classifier} model with {isGrouped} setting")
    classifier.test(isHeldOut=isHeldOut, isGrouped=isGrouped, use_bert=use_bert)


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
