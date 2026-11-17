from fastapi import FastAPI, HTTPException

from generation import build_prompt, generate_answer
from ingestion import ingest_documents
from models import AskRequest, AskResponse, IngestRequest, IngestResponse
from retrieval import has_relevant_context, retrieve

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
def ask(request: AskRequest) -> AskResponse:
    try:
        chunks = retrieve(request.question, INDEX_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index not found. Call /ingest first")
    if not has_relevant_context(chunks):
        return AskResponse(answer="I don't know", sources=[])
    answer = generate_answer(build_prompt(request.question, chunks))
    sources = list(dict.fromkeys(chunk["source"] for chunk in chunks))
    return AskResponse(answer=answer, sources=sources)

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