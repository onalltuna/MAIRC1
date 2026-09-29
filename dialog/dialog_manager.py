import joblib
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertModel
import torch
import classifiers.rule_based as rb
import classifiers.ml_classifier_1 as mlp
import classifiers.ml_classifier_2 as lr


def manage(classifier_name, is_grouped, use_bert):
    print(f"welcome to dialog manager, you are using {classifier_name} classifier.")
