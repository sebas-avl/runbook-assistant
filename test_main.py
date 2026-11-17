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

def test_ask(monkeypatch):
    fake_chunks = [{"text": "A Pod is the smallest unit.", "source": "pods.md", "score": 0.8}]
    monkeypatch.setattr("main.retrieve", lambda question, index_dir: fake_chunks)
    monkeypatch.setattr("main.generate_answer", lambda prompt: "fake answer")
    response = client.post("/ask", json={"question": "what is a pod?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "fake answer", "sources": ["pods.md"]}

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

def test_ask_without_relevant_context(monkeypatch):
    fake_chunks = [{"text": "A Pod is the smallest unit.", "source": "pods.md", "score": 0.1}]
    monkeypatch.setattr("main.retrieve", lambda question, index_dir: fake_chunks)
    
    # Trap: if /ask calls the text model, this makes the test fail.
    def fail_if_called(prompt):
        raise AssertionError("the text model must not be called")

    monkeypatch.setattr("main.generate_answer", fail_if_called)
    response = client.post("/ask", json={"question": "What is the best pizza recipe?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "I don't know", "sources": []}

def test_ask_without_index(tmp_path, monkeypatch):
    monkeypatch.setattr("main.INDEX_DIR", str(tmp_path / "no-index"))
    response = client.post("/ask", json={"question": "What is a Pod?"})
    assert response.status_code == 404

def test_ask_rejects_missing_question():
    response = client.post("/ask", json={})
    assert response.status_code == 422