import joblib
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertModel
import torch
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as ml1
import classifiers.ml_classifier_2 as ml2

classifiers = {
    "rulebased": rb,
    "ml1": ml1,
    "ml2": ml2,
}


def manage(classifier_name, is_grouped, use_bert):
    classifier = classifiers[classifier_name]
    print(f"\nWelcome to prompt manager! You are using the {classifier.name} classifier.")
    print("Type an utterance to classify. Type /exit or press Ctrl+C to exit.\n")

    while True:
        try:
            utterance = input("> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting dialog manager")
            break

        if not utterance:
            continue

        if utterance == "/exit":
            print("Exiting dialog manager")
            break

        try:
            if classifier_name == "rulebased":
                pred = rb.predict(utterance)
            elif classifier_name == "ml1":
                pred = ml1.predict(utterance=utterance, isGrouped=is_grouped, use_bert=use_bert)
            else:
                pred = ml2.predict(utterance=utterance, isGrouped=is_grouped, use_bert=use_bert)
        except FileNotFoundError as e:
            print(f"\nError: could not find a required model file: '{e.filename}'.")
            print("Make sure you've trained this classifier configuration first, e.g.:")
            print(f"  python main.py train --classifier {classifier_name} --grouped {'y' if is_grouped else 'n'}"
                  f"{' --bert y' if use_bert else ''}")
            break

        print(f"Predicted dialog act: {pred}\n")


def get_model_paths(classifier_name, is_grouped, use_bert):
    if classifier_name == "rulebased":
        return None, None

    group_suffix = "grouped" if is_grouped else "original"
    repr_suffix = "bert" if use_bert else None
    base_name = "MLP" if classifier_name == "ml1" else "LR"

    model_path = (
        f"classifiers/{base_name}_{repr_suffix}_{group_suffix}.joblib"
        if use_bert
        else f"classifiers/{base_name}_{group_suffix}.joblib"
    )
    vectorizer_path = (
        None
        if use_bert
        else f"classifiers/{base_name}_vectorizer_{group_suffix}.joblib"
    )

    return model_path, vectorizer_path


def encode_bert(texts):
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    bert_model = DistilBertModel.from_pretrained("distilbert-base-uncased")
    bert_model.eval()

    encoded = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

    with torch.no_grad():
        outputs = bert_model(**encoded)
        hidden = outputs.last_hidden_state 

    embeddings = hidden.mean(dim=1)
    return embeddings.numpy()
