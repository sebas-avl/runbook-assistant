from vector_store import build_index, load_index, save_index, search

VECTORS = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
CHUNKS = [
    {"text": "a", "source": "x.md"},
    {"text": "b", "source": "y.md"},
    {"text": "c", "source": "z.md"},
]


def test_build_index_counts_vectors():
    index = build_index(VECTORS)
    assert index.ntotal == 3


def test_search_returns_closest_first():
    index = build_index(VECTORS)
    results = search(index, CHUNKS, [1.0, 0.1], k=2)
    assert [r["text"] for r in results] == ["a", "c"]


def test_save_and_load_roundtrip(tmp_path):
    index = build_index(VECTORS)
    save_index(index, CHUNKS, str(tmp_path))
    loaded_index, loaded_chunks = load_index(str(tmp_path))
    assert loaded_index.ntotal == 3
    assert loaded_chunks == CHUNKS

def test_search_skips_missing_results():
    index = build_index(VECTORS)
    results = search(index, CHUNKS, [1.0, 0.1], k=5)
    assert len(results) == 3