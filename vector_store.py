import json
from pathlib import Path

import faiss
import numpy as np


def build_index(vectors: list[list[float]]) -> faiss.IndexFlatIP:
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)
    dimension = matrix.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(matrix)
    return index

def save_index(index: faiss.IndexFlatIP, chunks: list[dict[str, str]], directory: str) -> None:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path / "index.faiss"))
    (path / "metadata.json").write_text(json.dumps(chunks), encoding="utf-8")

def load_index(directory: str) -> tuple[faiss.IndexFlatIP, list[dict[str, str]]]:
    path = Path(directory)
    index = faiss.read_index(str(path / "index.faiss"))
    chunks = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    return index, chunks

def search(
    index: faiss.IndexFlatIP,
    chunks: list[dict[str, str]],
    query_vector: list[float],
    k: int = 3,
) -> list[dict]:
    query = np.array([query_vector], dtype="float32")
    faiss.normalize_L2(query)
    scores, ids = index.search(query, k)
    results = []
    for score, chunk_id in zip(scores[0], ids[0]):
        if chunk_id == -1:
            continue
        result = dict(chunks[chunk_id])
        result["score"] = float(score)
        results.append(result)
    return results