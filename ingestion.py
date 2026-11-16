from pathlib import Path

from chunking import chunk_text
from embeddings import embed_text
from vector_store import build_index, save_index


def build_chunks(document_names: list[str], docs_dir: str) -> list[dict[str, str]]:
    base = Path(docs_dir).resolve()
    chunks = []
    for name in document_names:
        path = (base / name).resolve()
        if base not in path.parents:
            raise ValueError(f"Invalid document name: {name}")
        text = path.read_text(encoding="utf-8")
        for piece in chunk_text(text):
            chunks.append({"text": piece, "source": name})
    return chunks

def ingest_documents(document_names: list[str], docs_dir: str, index_dir: str) -> int:
    chunks = build_chunks(document_names, docs_dir)
    if not chunks:
        raise ValueError("No text to ingest")
    vectors = [embed_text(chunk["text"]) for chunk in chunks]
    index = build_index(vectors)
    save_index(index, chunks, index_dir)
    return len(chunks)