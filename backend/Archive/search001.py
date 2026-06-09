from typing import Dict, List

import chromadb
from sentence_transformers import SentenceTransformer

from config import CHROMA_PATH, COLLECTION_NAME, EMBEDDING_MODEL_NAME, TOP_K
from config import MAX_DISTANCE as CONFIG_MAX_DISTANCE
from ingestion import normalize_text

_model = None
_collection = None




def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection

# Bereinigt die Nutzeranfrage, um irrelevante Phrasen zu entfernen, die die Suche stören könnten.
def clean_query_for_search(query: str) -> str:
    query = query.lower()

    remove_phrases = [
        "do we have",
        "have we sold",
        "have we ever sold",
        "did we sell",
        "did we ever sell",
        "was sold",
        "sold",
        "quoted",
        "have we quoted",
        "did we quote",
        "ever",
        "in the last years",
        "in recent years",
        "over the last years",
        "is there",
        "are there",
        "exists",
        "exist",
        "product",
        "products",
        "item",
        "items",
    ]

    for phrase in remove_phrases:
        query = query.replace(phrase, " ")

    return query.strip()


def search_products(query: str, top_k: int = TOP_K) -> Dict:
    model = get_model()
    collection = get_collection()

    normalized_query = normalize_text(clean_query_for_search(query))
    query_embedding = model.encode(normalized_query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits: List[Dict] = []
    for doc, metadata, distance in zip(
        results.get("documents", [[]])[0],
        results.get("metadatas", [[]])[0],
        results.get("distances", [[]])[0],
    ):
        hits.append(
            {
                "sku": metadata.get("sku"),
                "quantity": metadata.get("quantity"),
                "source_pdf": metadata.get("source_pdf"),
                "filename": metadata.get("filename"),
                "page": metadata.get("page"),
                "offer_number": metadata.get("offer_number"),
                "year_folder": metadata.get("year_folder"),
                "distance": round(float(distance), 4),
                "matched_text": doc,
            }
        )

    valid_results = [
        hit for hit in hits
        if float(hit["distance"]) <= float(CONFIG_MAX_DISTANCE)
    ]

    sold = len(valid_results) > 0

    return {
        "query": query,
        "sold": sold,
        "max_distance": float(CONFIG_MAX_DISTANCE),
        "results": valid_results,
    }
