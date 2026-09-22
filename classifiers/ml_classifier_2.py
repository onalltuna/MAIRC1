import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score

def load_data(path):
    data = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            act, utterance = line.split(maxsplit=1)
            data.append({"act": act.lower(), "utterance": utterance.lower()})
    return pd.DataFrame(data)

def evaluate(df):
    y_true, y_pred = df["act"], df["pred"]
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_true, y_pred):.4f}")

def save_model(vectorizer, clf, suffix):
    joblib.dump(vectorizer, f"classifiers/LR_vectorizer_{suffix}.joblib")
    joblib.dump(clf, f"classifiers/LR_{suffix}.joblib")

def load_model(suffix):
    vectorizer = joblib.load(f"classifiers/LR_vectorizer_{suffix}.joblib")
    clf = joblib.load(f"classifiers/LR_{suffix}.joblib")
    return vectorizer, clf

def train(isGrouped):
    print("you are running the train process for ML2")
    print(f"isGrouped: {isGrouped}")

    suffix = "grouped" if isGrouped else "original"
    if isGrouped:
        data_path = "data/processed/grouped_train.dat"
    else:
        data_path = "data/processed/original_train.dat"

    df = load_data(data_path)
    utterances = df["utterance"].tolist()
    acts = df["act"].tolist()

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2  # ignore rare words
    )
    utterances_vec = vectorizer.fit_transform(utterances)

    clf = LogisticRegression(
        solver="lbfgs",  # supports multiclass
        max_iter=1000,
        class_weight="balanced"
    )
    clf.fit(utterances_vec, acts)
    save_model(vectorizer, clf, suffix)

def test(isHeldOut, isGrouped):
    print("you are testing ML2")
    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}")

    suffix = "grouped" if isGrouped else "original"
    if isHeldOut:
        data_path = "data/raw/fake_dialog_acts_test.dat"
    else:
        data_path = f"data/processed/{suffix}_test.dat"

    df = load_data(data_path)
    vectorizer, clf = load_model(suffix)

    utterances = vectorizer.transform(df["utterance"])
    preds = clf.predict(utterances)
    df["pred"] = preds
    evaluate(df)