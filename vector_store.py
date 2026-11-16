import faiss
import numpy as np


def build_index(vectors: list[list[float]]) -> faiss.IndexFlatIP:
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)
    dimension = matrix.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(matrix)
    return index