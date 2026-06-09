# TAGACA RAG MVP Backend

Lokales MVP für PDF-Ingestion, Embeddings, ChromaDB-Suche und LLM-Antworten über Ollama/Llama3.

## Zielstruktur

```text
ChatBot/
├── tagaca_mvp_pdfs/
│   ├── 2021/
│   ├── 2022/
│   └── ...
├── backend/
│   ├── api.py
│   ├── ingestion.py
│   ├── search.py
│   ├── llm.py
│   ├── config.py
│   └── requirements.txt
├── chroma_db/              # wird automatisch erzeugt
└── processed_files.json    # wird automatisch erzeugt
```

## Installation

```bash
cd U:\Backup\ChatBot\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ollama vorbereiten

```bash
ollama pull llama3
ollama serve
```

Falls `ollama serve` sagt, dass Ollama schon läuft, ist das okay.

## Backend starten

```bash
uvicorn api:app --reload --port 8000
```

## PDFs importieren

Im Browser oder per Postman:

```text
POST http://localhost:8000/ingest
```

Force-Reimport:

```text
POST http://localhost:8000/ingest?force=true
```

## Suchen ohne LLM

```text
GET http://localhost:8000/search?query=kit PCR EBV
```

## Chat mit LLM

```text
POST http://localhost:8000/chat
```

Body:

```json
{
  "query": "¿Se ha vendido alguna vez un kit PCR para EBV?",
  "top_k": 5
}
```

## Wichtiger Hinweis

Dieses MVP nutzt einen einfachen Parser. Für echte 50.000 PDFs sollte später ein robuster Produktzeilen-Parser gebaut werden.
