from fastapi.testclient import TestClient

from main import app

client = TestClient(app) #creates an instance of TestClient that is connected to my real app

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200  #succesful
    assert response.json() == {"status":"ok"}

#Note: a line empty between two imports because of Ruff function (it is a convention)