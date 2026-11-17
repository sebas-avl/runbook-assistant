from embeddings import embed_text
from vector_store import load_index, search

MIN_SCORE = 0.25


def has_relevant_context(chunks: list[dict]) -> bool:
    return bool(chunks) and chunks[0]["score"] >= MIN_SCORE

def retrieve(question: str, index_dir: str, k: int = 3) -> list[dict]:
    index, chunks = load_index(index_dir)
    query_vector = embed_text(question)
    return search(index, chunks, query_vector, k)