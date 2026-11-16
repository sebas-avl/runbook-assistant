from fastapi.testclient import TestClient

from main import app

client = TestClient(app) #creates an instance of TestClient that is connected to my real app

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200  #succesful
    assert response.json() == {"status":"ok"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message":"Runbook Assistant"}

def test_ask():
    response = client.post("/ask", json={"question": "what is kubernetes?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "this is an example answer", "sources": ["example.md"]}

def test_ingest(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "doc1.md").write_text("hello world " * 100, encoding="utf-8")
    monkeypatch.setattr("main.DOCS_DIR", str(docs_dir))
    monkeypatch.setattr("main.INDEX_DIR", str(tmp_path / "index"))
    monkeypatch.setattr("ingestion.embed_text", lambda text: [1.0, 0.0, 0.0])

    response = client.post("/ingest", json={"documents": ["doc1.md"]})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["documents_count"] == 1
    assert body["chunks_count"] > 0
    assert (tmp_path / "index" / "index.faiss").exists()

def test_ingest_document_not_found():
    response = client.post("/ingest", json={"documents": ["nope.md"]})
    assert response.status_code == 404

def test_ingest_rejects_path_traversal():
    response = client.post("/ingest", json={"documents": ["../README.md"]})
    assert response.status_code == 400