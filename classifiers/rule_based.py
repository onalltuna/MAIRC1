import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score
# To do: maybe use regex for rules
rules = {
    "ack": ["kay", "good", "fine"],
    "affirm": ["right", "yes", "yeah", "ye", "yea", "correct", "perfect"],
    "bye": ["goodbye", "good bye", "that's all", "thats all", "bye"],
    "confirm": ["is that", "do they", "does it", "is this", "is there", "is it"],
    "deny": ["dont", "don't", "wrong", "no"],
    "hello": ["hello", "hi", "welcome"],
    "inform": ["any", "i dont care", "i don't care", "i am looking for", "im looking for"],
    "negate": ["no", "not"],
    "repeat": ["again", "repeat", "go back", "back"],
    "reqalts": ["anything else", "what else", "how about", "what about", "is there", "are there", "can you tell me", "next one", "another", "other", "different", "more", "do you have any", "is that the only one with", "what is available"],
    "reqmore": ["more"],
    "restart": ["start over", "start again", "reset"],
    "thankyou": ["thanks", "thank you"],
    "request": ["what is", "whats", "can i get", "could i get", "may i get", "can i have", "could i have", "may i have", "can i know", "could i know", "may i know", "can you give me", "what about", "what kind of", "what type of", "do you have", "what part of town", "what area is", "what area is it in", "where", "i would like", "could you", "i need", "how about", "how much", "phone number", "address", "price", "post code", "location"],
    "null": ["noise", "cough", "unintelligible", "breathing", "inaudible", "breathing"]
}

def evaluate(df):
    y_true = df["act"]
    y_pred = df["pred"]
    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy}")
    print(f"Balanced Accuracy: {balanced_accuracy}")


def train(isGrouped):
    # TODO Not sure if this function is actually necessary becuase training rule_based is coming up with the rules and
    # that is a manual job
    print("You are running the train proccess for Rule Based Classifier")
    print(f"Current rules are as follows: {rules}")
    print("\nTo manually modify the rules please visit classifiers/rule_based.py\n")


def test(isHeldOut, isGrouped):
    # TODO this function should reach the pretrained model(in the case of rule_based the rule dict and test data)

    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}")
    if isHeldOut:
        data_path = "data/raw/fake_dialog_acts_test.dat"
    elif isGrouped:
        data_path = "data/processed/grouped_test.dat"
    elif  not isGrouped:
        data_path = "data/processed/original_test.dat"
    

    data = []
    with open(data_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            act, utterance = line.split(maxsplit=1)
            # lowercasing is applied but it this can be removed depending on the real test data
            data.append({"act": str.lower(act), "utterance": str.lower(utterance)})

    df = pd.DataFrame(data=data)

    # print(f"different acts in test_df: {df["act"].unique()}")

    df["pred"] = None

    # currently this logic only checks if the rule word is present in the utterance and if not mark it as null type
    # this can also be modified in the future
    # To do: how to solve overlapping keywords from different acts? How to deal with act "null"?
    for index, row in df.iterrows():
        words = row["utterance"].split()
        combos = all_ngrams(words=words)
        # print(f"words: {words}")
        df.loc[index, "pred"] = "inform"
        for act, keywords in rules.items():
            for keyword in keywords:
                # print(f"keyword: {keyword}")
                # print(f"words: {words}")
                # print(f"combos: {combos}")
                if keyword in combos:
            # if any(keyword in words for keyword in keywords):
                    df.loc[index, "pred"] = act
                    break

    # print(f"different preds in test_df: {df["pred"].unique()}")

    evaluate(df)





def all_ngrams(words):
    n = len(words)
    combos = []
    for length in range(1, n + 1):          # window size: 1, 2, 3, ... up to full length
        for start in range(0, n - length + 1):  # slide the window across
            combos.append(" ".join(words[start:start + length]))
    return combos


