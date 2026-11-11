from fastapi import FastAPI

from models import AskRequest, AskResponse, IngestRequest, IngestResponse

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.get("/")
def root():
    return {"message":"Runbook Assistant"}

@app.post("/ask")
def ask(request:AskRequest) -> AskResponse:
    return AskResponse(answer = "this is an example answer", sources=["example.md"])

@app.post("/ingest")
def ingest(request:IngestRequest) -> IngestResponse:
    return IngestResponse(status="ok", documents_count=len(request.documents))
