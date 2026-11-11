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

def test_ingest():
    response = client.post("/ingest", json={"documents": ["doc1.md", "doc2.md"]})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "documents_count": 2}
#Note: a line empty between two imports because of Ruff function (it is a convention)