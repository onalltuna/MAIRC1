#TODO in this file first ML classifier should be defined, its train function should reach the train data in data folder and train the model
#when the model is trained, it should be saved under classifiers folder. When the test funcion is called it should load the respective model from 
# classifiers folder and reach the test data from data folder and apply the testing logic

from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.neural_network import MLPClassifier
import joblib
from sklearn.metrics import accuracy_score, balanced_accuracy_score
import torch
from transformers import DistilBertModel, DistilBertTokenizerFast

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

def train(isGrouped, use_bert):
    print("You are running the train process for MLP with BoW")
    print(f"isGrouped: {isGrouped}, use_bert: {use_bert}")

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


def test(isHeldOut, isGrouped, use_bert):
    print("You are testing ML classifier 1")
    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}, use_bert: {use_bert}")

    suffix = ("bert_" if use_bert else "") + ("grouped" if isGrouped else "original")
    data_path = (
        "data/raw/fake_dialog_acts_test.dat" #TODO change this to the correct file_name later
        if isHeldOut else
        f"data/processed/{'grouped' if isGrouped else 'original'}_test.dat"
    )

    df = load_data(data_path)

    if use_bert:
        X_test_bow = encode_bert(df["utterance"].tolist())
    else:
        vectorizer = joblib.load(f"classifiers/MLP_vectorizer_{suffix}.joblib")
        X_test_bow = vectorizer.transform(df["utterance"])

    clf = joblib.load(f"classifiers/MLP_{suffix}.joblib")
    preds = clf.predict(X_test_bow)
    df["pred"] = preds
    evaluate(df)


def evaluate(df):
    y_true, y_pred = df["act"], df["pred"]
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_true, y_pred):.4f}")


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