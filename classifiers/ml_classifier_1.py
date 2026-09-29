from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.neural_network import MLPClassifier
import joblib
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
import numpy as np
import torch
from transformers import DistilBertModel, DistilBertTokenizerFast
from transformers.utils import logging

logging.set_verbosity_error()

name = "MLP"


def encode_bert(texts, batch_size=32, max_length=128):

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    bert_model = DistilBertModel.from_pretrained("distilbert-base-uncased")
    bert_model.eval()

    all_embeddings = []

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

def train(isGrouped, use_bert):

    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")

    # Select the training file depending on grouped or not
    if isGrouped:
        data_path = "data/processed/grouped_train.dat"
    else:
        data_path = "data/processed/original_train.dat"

    df = load_data(data_path)

    X_text = df["utterance"].tolist()
    y = df["act"].tolist()

    if use_bert:
        X_bow = encode_bert(X_text)
        vectorizer = None
    else:
        # Use CountVectorizer to create BoW
        vectorizer = CountVectorizer()
        X_bow = vectorizer.fit_transform(X_text)

    # Define the MLP classifier (with 1 hidden layer) and train
    clf = MLPClassifier(hidden_layer_sizes=(128,), max_iter=300, random_state=42)
    clf.fit(X_bow, y)

    # Save the classifier and the vectorizer
    joblib.dump(clf, f"classifiers/MLP_{suffix}.joblib")
    if not use_bert:
        joblib.dump(vectorizer, f"classifiers/MLP_vectorizer_{suffix}.joblib")
    
    print(f"The {name} model has been successfully trained!")


def test(isHeldOut, isGrouped, use_bert):

    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")
    data_path = (
        "data/raw/dialog_acts_test.dat"
        if isHeldOut else
        f"data/processed/{'grouped' if isGrouped else 'original'}_test.dat"
    )

    try:
        df = load_data(data_path)
    except FileNotFoundError:
        print(f"Error: test data file not found at '{data_path}'.")
        if isHeldOut:
            print("Make sure the held-out file exists at that path.")
        else:
            print("Make sure you've run data_preprocess.py to generate the processed data files.")
        return
    except OSError as e:
        print(f"Error: could not read '{data_path}': {e}")
        return

    try:
        if use_bert:
            X_test_bow = encode_bert(df["utterance"].tolist())
        else:
            vectorizer = joblib.load(f"classifiers/MLP_vectorizer_{suffix}.joblib")
            X_test_bow = vectorizer.transform(df["utterance"])

        clf = joblib.load(f"classifiers/MLP_{suffix}.joblib")
    except FileNotFoundError as e:
        print(f"\nError: could not find the required model file: '{e.filename}'.")
        print("Make sure you've trained this classifier with the respective settings firs, e.g.:")
        print(f"  python main.py train --classifier ml1 --grouped {'y' if isGrouped else 'n'}"
              f"{' --bert y' if use_bert else ''}")
        return

    preds = clf.predict(X_test_bow)
    df["pred"] = preds
    evaluate(df)


def evaluate(df):
    y_true, y_pred = df["act"], df["pred"]
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1: {f1_score(y_true, y_pred, average="macro"):.4f}")


def predict(utterance, isGrouped, use_bert):
    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")

    if use_bert:
        features = encode_bert([utterance])
    else:
        vectorizer = joblib.load(f"classifiers/MLP_vectorizer_{suffix}.joblib")
        features = vectorizer.transform([utterance])

    clf = joblib.load(f"classifiers/MLP_{suffix}.joblib")
    pred = clf.predict(features)[0]

    return pred