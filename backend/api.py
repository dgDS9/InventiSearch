from typing import Optional
from starlette.responses import JSONResponse

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingestion import ingest_pdfs
from llm import ask_llm
from search import search_products

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title="Testing RAG-System/LLM", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pablomedito.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )

app.add_middleware(SlowAPIMiddleware)


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
@limiter.limit("20/hour")
def chat(request: Request, chat_request: ChatRequest):
    if len(chat_request.query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail="Query too long.")

    top_k = min(chat_request.top_k or 10, MAX_TOP_K)

    search_result = search_products(chat_request.query, top_k)

    if not search_result["sold"]:
        return {
            "query": chat_request.query,
            "sold": False,
            "answer": "No, no products sold were found that sufficiently match your search.",
            "sources": []
        }

    try:
        answer = ask_llm(chat_request.query, search_result)
    except Exception:
        answer = (
        "Product matches were found successfully. However, the AI explanation is temporarily unavailable because "
        "the free daily quota of Google Gemini has been reached. Please try again later."
    )

    return {
        "query": chat_request.query,
        "sold": search_result["sold"],
        "answer": answer,
        "sources": search_result["results"],
    }


@app.get("/")
def root():
    return {"app": "RAG/LLM Backend", "status": "running"}