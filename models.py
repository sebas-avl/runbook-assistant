from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


class IngestRequest(BaseModel):
    documents: list[str]


class IngestResponse(BaseModel):
    status: str
    documents_count: int