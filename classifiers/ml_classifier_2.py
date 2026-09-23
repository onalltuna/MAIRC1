import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertModel
import torch

def encode_bert(texts):
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    bert_model = DistilBertModel.from_pretrained("distilbert-base-uncased")
    bert_model.eval()

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = bert_model(**encoded)
        hidden = outputs.last_hidden_state

    embeddings = hidden.mean(dim=1)
    return embeddings.numpy()

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

def train(isGrouped, use_bert):
    print("You are running the train process for ML classifier2")
    print(f"isGrouped: {isGrouped}, user_bert: {use_bert}")

    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")
    if isGrouped:
        data_path = "data/processed/grouped_train.dat"
    else:
        data_path = "data/processed/original_train.dat"

    df = load_data(data_path)
    utterances = df["utterance"].tolist()
    acts = df["act"].tolist()

    if use_bert:
        utterances_vec = encode_bert(utterances)
        vectorizer = None
    else:
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

    joblib.dump(clf, f"classifiers/LR_{suffix}.joblib")
    if not use_bert:
        joblib.dump(vectorizer, f"classifiers/LR_vectorizer_{suffix}.joblib")

def test(isHeldOut, isGrouped, use_bert):
    print("You are testing ML classifier2")
    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}, use_bert: {use_bert}")

    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")
    data_path = (
        "data/raw/fake_dialog_acts_test.dat"
        if isHeldOut else
        f"data/processed/{'grouped' if isGrouped else 'original'}_test.dat"
    )

    df = load_data(data_path)

    if use_bert:
        utterances = encode_bert(df["utterance"].tolist())
    else:
        vectorizer = joblib.load(f"classifiers/LR_vectorizer_{suffix}.joblib")
        utterances = vectorizer.transform(df["utterance"])

    clf = joblib.load(f"classifiers/LR_{suffix}.joblib")
    preds = clf.predict(utterances)
    df["pred"] = preds
    evaluate(df)


def predict(utterance, isGrouped, use_bert):
    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")

    if use_bert:
        features = encode_bert([utterance])
    else:
        vectorizer = joblib.load(f"classifiers/LR_vectorizer_{suffix}.joblib")
        features = vectorizer.transform([utterance])

    clf = joblib.load(f"classifiers/LR_{suffix}.joblib")
    pred = clf.predict(features)[0]

    return pred