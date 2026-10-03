import numpy as np
import torch
from transformers import DistilBertTokenizerFast, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity
from dialog.ontology import ONTOLOGY

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
bert_model = DistilBertModel.from_pretrained("distilbert-base-uncased")
bert_model.eval()

def encode_bert(texts, batch_size=32, max_length=128):
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

ONTOLOGY_EMBEDDINGS = {
    slot: encode_bert(values)
    for slot, values in ONTOLOGY.items()
}

def find_semantic_match(
    candidate: str,
    slot: str,
    threshold: float = 0.7,
):
    """
    Find the closest ontology value semantically to candidate.

    Returns:
        (best_value, best_score) or None if the best score is below threshold.
    """
    candidate_embedding = encode_bert([candidate])

    ontology_values = ONTOLOGY[slot]
    ontology_embeddings = ONTOLOGY_EMBEDDINGS[slot]

    similarities = cosine_similarity(
        candidate_embedding,
        ontology_embeddings
    )[0]

    best_index = np.argmax(similarities)
    best_score = similarities[best_index]
    best_value = ontology_values[best_index]

    # Reject matches that are too far away
    if best_score < threshold:
        return None

    return best_value, float(best_score)