#TODO in this file first ML classifier should be defined, its train function should reach the train data in data folder and train the model
#when the model is trained, it should be saved under classifiers folder. When the test funcion is called it should load the respective model from 
# classifiers folder and reach the test data from data folder and apply the testing logic

from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
from sklearn.neural_network import MLPClassifier
import joblib
import os
from sklearn.metrics import accuracy_score, balanced_accuracy_score



def train(isGrouped):
    print("You are running the train proccess for MLP with BoW")
    print(f"isGrouped: {isGrouped}")

    # select the training file depending on grouped or not
    if isGrouped:
        data_path = "data/processed/grouped_train.dat"
        suffix = "grouped"
    else:
        data_path = "data/processed/original_train.dat"
        suffix = "notgrouped"

    data = []
    with open(data_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            act, utterance = line.split(maxsplit=1)
            # lowercasing is applied but it is already applied during pre-processing so this part can be changes
            data.append({"act": str.lower(act), "utterance": str.lower(utterance)})

    df = pd.DataFrame(data=data)

    X_text = df["utterance"].tolist()
    y = df["act"].tolist()

    # use CountVectorizer to create BoW
    vectorizer = CountVectorizer()
    X_bow = vectorizer.fit_transform(X_text)

    # print(f"X_bow: {X_bow}")

    # define the MLP classifier and train
    # MLP with 1 hidden layer
    clf = MLPClassifier(hidden_layer_sizes=(128,), max_iter=300, random_state=42)
    clf.fit(X_bow, y)


    # save the classifier and the vectorizer
    joblib.dump(vectorizer, f"classifiers/bow_vectorizer_{suffix}.joblib")
    joblib.dump(clf, f"classifiers/mlp_bow_{suffix}.joblib")




def train_bert():
    print("You are training a MLP with pre-trained BERT embeddings")


def test(isHeldOut, isGrouped):
    print("you are testing ML1")
    print(f"isHeldOut: {isHeldOut}, isGrouped: {isGrouped}")

    if isGrouped:
        data_path = "data/processed/grouped_test.dat"
        suffix = "grouped"
    else:
        data_path = "data/processed/original_test.dat"
        suffix = "notgrouped"

    if isHeldOut:
        data_path = "data/raw/fake_dialog_acts_test.dat" #TODO change this to the correct file_name later

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


    print(f"suffix: {suffix}")
    vectorizer = joblib.load(f"classifiers/bow_vectorizer_{suffix}.joblib")
    clf = joblib.load(f"classifiers/mlp_bow_{suffix}.joblib")
    X_test_bow = vectorizer.transform(df["utterance"]) # turn utterance words into numeric representations
    preds = clf.predict(X_test_bow)
    df["pred"] = preds
    evaluate(df)



def evaluate(df):
    y_true = df["act"]
    y_pred = df["pred"]
    accuracy = accuracy_score(y_true, y_pred)
    balanced_accuracy = balanced_accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy}")
    print(f"Balanced Accuracy: {balanced_accuracy}")