import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dialog.ontology import ONTOLOGY
from classifiers.bert_encoder import encode_bert

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