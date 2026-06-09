from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Root-Ordner: ChatBot/backend/config.py -> ChatBot
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# PDF-Ordner liegt laut Screenshot direkt im ChatBot-Root
PDF_ROOT = PROJECT_ROOT / r"C:\Users\Daniela.Gaer\Desktop\Neu\InventiSearch\samplecompany_quotation_pdfs"

# Lokale Speicherorte
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
PROCESSED_FILES_PATH = PROJECT_ROOT / "processed_files.json"

# Collection-Name in ChromaDB
COLLECTION_NAME = "samplecompany_quotations"

# Lokales Embedding-Modell
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# # Ollama / Llama3
# OLLAMA_URL = "http://localhost:11434/api/chat"
# OLLAMA_MODEL = "llama3"

# LLM Gemini-2.5-flash
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "120"))
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "500"))

# Distanz-Schwelle: kleiner = ähnlicher.
# Für MVP später mit echten Tests feinjustieren.
MAX_DISTANCE = 1.2
TOP_K = 10

