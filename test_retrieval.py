from retrieval import retrieve
from vector_store import build_index, save_index


def test_retrieve_returns_closest_chunks(tmp_path, monkeypatch):
    chunks = [
        {"text": "a", "source": "x.md"},
        {"text": "b", "source": "y.md"},
        {"text": "c", "source": "z.md"},
    ]
    index = build_index([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    save_index(index, chunks, str(tmp_path))
    monkeypatch.setattr("retrieval.embed_text", lambda text: [1.0, 0.1])

    results = retrieve("any question", str(tmp_path), k=2)

    assert [r["text"] for r in results] == ["a", "c"]