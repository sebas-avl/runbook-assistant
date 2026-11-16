from fastapi import FastAPI, HTTPException

from ingestion import ingest_documents
from models import AskRequest, AskResponse, IngestRequest, IngestResponse

app = FastAPI()

DOCS_DIR = "data/docs"
INDEX_DIR = "data/index"

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
    try:
        chunks_count = ingest_documents(request.documents, DOCS_DIR, INDEX_DIR)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    return IngestResponse(
        status="ok",
        documents_count=len(request.documents),
        chunks_count=chunks_count,
    )