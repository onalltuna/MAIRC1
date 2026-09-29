import pandas as pd
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from transformers import DistilBertTokenizerFast, DistilBertModel
import numpy as np
import torch

from transformers.utils import logging

logging.set_verbosity_error()

name = "LogisticRegression"


def encode_bert(texts, batch_size=32, max_length=128):
    all_embeddings = []
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    bert_model = DistilBertModel.from_pretrained("distilbert-base-uncased")
    bert_model.eval()

    for i in range(0, len(texts), batch_size):

        batch = texts[i:i + batch_size]

        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt"
        )

        with torch.no_grad():

            outputs = bert_model(**encoded)
            hidden = outputs.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1)
            masked_hidden = hidden * mask
            summed = masked_hidden.sum(dim=1)
            counts = mask.sum(dim=1)
            embeddings = summed / counts

        all_embeddings.append(embeddings.cpu().numpy())

    return np.vstack(all_embeddings)

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
    print(f"\nAccuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1: {f1_score(y_true, y_pred, average="macro"):.4f}")


def train(isGrouped, use_bert):
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
        vectorizer = CountVectorizer()
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
    print(f"The {name} model has been successfully trained!")

def test(isHeldOut, isGrouped, use_bert):
    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")
    data_path = (
        "data/raw/dialog_acts_test.dat"
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