from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion import ingest_pdfs
from llm import ask_llm
from search import search_products

app = FastAPI(title="Testing RAG-System/LLM", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MAX_TOP_K = 10
MAX_QUERY_LENGTH = 1000

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 10


@app.get("/health")
def health():
    return {"status": "ok", "service": "RAG-System/LLM Backend"}


@app.post("/ingest")
def ingest(force: bool = Query(False, description="True = PDFs erneut verarbeiten")):
    return ingest_pdfs(force=force)


@app.get("/search")
def search(query: str, top_k: int = 10):
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Query too long.")

    top_k = min(top_k, MAX_TOP_K)

    return search_products(query=query, top_k=top_k)


@app.post("/chat")
def chat(request: ChatRequest):
    if len(request.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Query too long.")

    top_k = min(request.top_k or 10, MAX_TOP_K)

    search_result = search_products(request.query, top_k)

    if not search_result["sold"]:
        return {
            "query": request.query,
            "sold": False,
            "answer": "No, no products sold were found that sufficiently match your search.",
            "sources": []
        }

    answer = ask_llm(request.query, search_result)

    return {
        "query": request.query,
        "sold": search_result["sold"],
        "answer": answer,
        "sources": search_result["results"],
    }


@app.get("/")
def root():
    return {"app": "RAG/LLM Backend", "status": "running"}