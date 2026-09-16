import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score

rules = {
    "inform": "food",
    "affirm": "yes",
    "request": "the",
    "thankyou": "thank",
    "null": "noise",
    "bye": "good",
    "reqalts": "about",
    "negate": "no",
    "confirm": "it",
    "hello": "hello",
    "repeat": "repeat",
    "ack": "okay",
    "deny": "wrong",
    "restart": "start",
    "reqmore": "more",
}

# this file path can change depending on the test data that TAs will be using
test_data_file_path = "data/processed/test/fake_test_data.dat"


def evaluate(df):
    y_true = df["act"]
    y_pred = df["pred"]
    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy}")
    print(f"Balanced Accuracy: {balanced_accuracy}")


def train():
    # TODO Not sure if this function is actually necessary becuase training rule_based is coming up with the rules and
    # that is a manual job
    print("You are running the train proccess for Rule Based Classifier")
    print(f"Current rules are as follows: {rules}")
    print("\nTo modify the rules please visit classifiers/rule_based.py\n")


def test():
    # TODO this function should reach the pretrained model(in the case of rule_based the rule dict and test data)

    data = []
    with open(test_data_file_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            act, utterance = line.split(maxsplit=1)
            # lowercasing is applied but it this can be removed depending on the real test data
            data.append({"act": str.lower(act), "utterance": str.lower(utterance)})

    df = pd.DataFrame(data=data)

    df["pred"] = None

    # currently this logic only checks if the rule word is present in the utterance and if not mark it as null type
    # this can also be modified in the future
    for index, row in df.iterrows():
        words = row["utterance"].split()

        for act, keyword in rules.items():
            if keyword in words:
                df.loc[index, "pred"] = act
                break
            else:
                df.loc[index, "pred"] = "null"

    evaluate(df)
