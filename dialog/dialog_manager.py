import joblib
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertModel
import torch
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as mlp
import classifiers.ml_classifier_2 as lr


def manage(classifier_name, is_grouped, use_bert):
    print(f"welcome to dialog manager, you are using {classifier_name} classifier.")

    # print(f"model_path: {model_path}")
    # print(f"vectorizer_path: {vectorizer_path}")

    print("Type an utterance to classify and press Ctrl+C to exit\n")

    while True:
        try:
            utterance = input("> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting dialog manager")
            break

        if not utterance:
            continue
        if classifier_name == "rulebased":
            pred = rb.predict(utterance)         
        elif classifier_name == "ml1":
            pred = mlp.predict(utterance=utterance,isGrouped=is_grouped,use_bert=use_bert)
        else:
            pred = lr.predict(utterance=utterance,isGrouped=is_grouped,use_bert=use_bert)

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
