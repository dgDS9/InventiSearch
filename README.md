# InventiSearch – Chatbot-/RAG-System

Backend/LLM: Daniela Gaer
Frontend: Pablo Medialdea Torres

Offical link to the Chatbot: https://pablomedito.github.io/InventiSearch/

InventiSearch is a intelligent search across biotechnology and laboratory quotation documents (PDF files).

The system processes quotation PDFs, extracts product information (SKU, product name, quantity, unit price, total price), generates embeddings using SentenceTransformers, stores them in ChromaDB, and answers user queries with Gemini 2.5 Flash.

## Project Structure

```text
InventiSearch/
├── samplecompany_quotation_pdfs/
│   ├── 2021/
│   ├── 2022/
│   ├── 2023/
│   ├── 2024/
│   ├── 2025/
│   └── 2026/
│
├── backend/
│   ├── api.py
│   ├── ingestion.py
│   ├── search.py
│   ├── llm.py
│   ├── config.py
│   └── requirements.txt
│
├── chroma_db/              # automatically generated
├── processed_files.json    # automatically generated
└── README.md
```

## Features

* PDF ingestion
* Automatic extraction of:

  * SKU
  * Product name
  * Quantity
  * Unit price
  * Total price
* Embeddings with SentenceTransformers
* Vector search with ChromaDB
* RAG (Retrieval-Augmented Generation) workflow
* Responses powered by Google Gemini 2.5 Flash
* Multilingual search queries (English / Spanish)
* Deployed on Linux servers (Hetzner)

## Installation

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=120
GEMINI_MAX_OUTPUT_TOKENS=1000
```

## Start the Backend

```bash
uvicorn api:app --reload --port 8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Import PDFs

```text
POST /ingest
```

Force a full re-import:

```text
POST /ingest?force=true
```

## Product Search Without LLM

```text
GET /search?query=PCR kit HPV
```

Example:

```text
GET /search?query=Gilson P200 Pipette
```

## Chat with Gemini

```text
POST /chat
```

Request:

```json
{
  "query": "Have we ever sold a Gilson P200 pipette?",
  "top_k": 5
}
```

## Technologies Used

* FastAPI
* ChromaDB
* SentenceTransformers
* Gemini 2.5 Flash
* PyMuPDF
* Python 3.11+

## Deployment

Production Infrastructure

The current Project is deployed on a Hetzner Ubuntu server and includes:

* GitHub repository for version control and deployments
* FastAPI backend with Swagger API documentation
* ChromaDB for vector storage and semantic search
* Google Gemini 2.5 Flash for answer generation
* systemd service for automatic startup and process management
* Nginx reverse proxy for secure request routing
* UFW firewall with only required ports exposed
* Dedicated Linux service user (inventisearch) instead of root (for security)
* Environment-based configuration via .env
* Rate limiting to reduce abuse and control LLM costs

## Notes

This repository contains only synthetic sample data.

All quotation PDFs, customers, company names, SKUs, and product information are intended solely for demonstration.

The following enhancements are recommended:

* More robust PDF parsing
* User management
* API authentication
* Database-backed chat history
* Monitoring and logging
* Automated re-indexing of new documents

```text
```
