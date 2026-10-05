import numpy as np
import torch
from transformers import DistilBertModel, DistilBertTokenizerFast
from transformers.utils import logging

logging.set_verbosity_error()

_tokenizer = None
_model = None


def _get_bert():
    global _tokenizer, _model
    if _model is None:
        _tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
        _model = DistilBertModel.from_pretrained("distilbert-base-uncased")
        _model.eval()
    return _tokenizer, _model


def encode_bert(texts, batch_size=32, max_length=128):
    tokenizer, model = _get_bert()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        encoded = tokenizer(batch, padding=True, truncation=True,
                            max_length=max_length, return_tensors="pt")
        with torch.no_grad():
            hidden = model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1)
            embeddings = (hidden * mask).sum(dim=1) / mask.sum(dim=1)
        all_embeddings.append(embeddings.cpu().numpy())

    return np.vstack(all_embeddings)