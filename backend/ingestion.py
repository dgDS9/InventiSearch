import hashlib
import json
import re
# akzentfreie Normalisierung für bessere Suche
import unicodedata
from pathlib import Path
from typing import Dict, List

import chromadb
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    PDF_ROOT,
    PROCESSED_FILES_PATH,
)


def load_processed_files() -> Dict[str, str]:
    if not PROCESSED_FILES_PATH.exists():
        return {}
    return json.loads(PROCESSED_FILES_PATH.read_text(encoding="utf-8"))


def save_processed_files(processed: Dict[str, str]) -> None:
    PROCESSED_FILES_PATH.write_text(
        json.dumps(processed, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def file_hash(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def extract_text_by_page(pdf_path: Path) -> List[Dict]:
    pages = []
    with fitz.open(pdf_path) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                pages.append({"page": page_index, "text": text})
    return pages

# Bereinigt die Produktbeschreibungstexte, um eine konsistentere Suche zu ermöglichen.
# Entfernt Sonderzeichen, normalisiert Akzente und konvertiert in Kleinbuchstaben.
# Dadurch sollen ähnliche Produkte trotz kleiner Textunterschiede gefunden werden.
# Beispiel: "Cámara de Fotos - Modelo X1000" -> "camara de fotos modelo x1000"
def normalize_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("µ", "u")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-záéíóúüñ0-9\-_/.,:;() %]+", " ", text)
    return text.strip()


def extract_offer_number(text: str) -> str:
    match = re.search(r"oferta\s*(?:n[ºo.]*)?\s*[:#]?\s*([a-z0-9\-_/]+)", text, re.IGNORECASE)
    return match.group(1) if match else "unknown"


def extract_product_lines(text: str) -> list[dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    products = []

    sku_pattern = re.compile(r"SKU:\s*([A-Z0-9\-]+)", re.IGNORECASE)
    price_pattern = re.compile(r"USD\s*[0-9,.]+", re.IGNORECASE)
    position_pattern = re.compile(r"^\d+\s+")
    stop_pattern = re.compile(r"(subtotal|vat|total offer|net subtotal|conditions|fictional)", re.IGNORECASE)

    for i, line in enumerate(lines):
        sku_match = sku_pattern.search(line)
        if not sku_match:
            continue

        sku = sku_match.group(1).upper()

        # Produktname meistens 1 Zeile über SKU
        product_name = lines[i - 1] if i > 0 else "unknown"

        block_lines = []
        for j in range(max(0, i - 1), min(len(lines), i + 6)):
            if j != i and sku_pattern.search(lines[j]):
                break
            if stop_pattern.search(lines[j]):
                break
            block_lines.append(lines[j])

        raw_product_text = " | ".join(block_lines)

        # Suche nach Zahlen und Preisen nach der SKU-Zeile
        following_text = " ".join(lines[i:min(len(lines), i + 8)])
        prices = price_pattern.findall(following_text)

        # Menge: erste isolierte Zahl nach SKU/Description
        quantity = None

        qty_match = re.search(r"\b(\d+)\s+USD\s*[0-9,.]+", following_text, re.IGNORECASE)

        if qty_match:
            quantity = int(qty_match.group(1))

        unit_price = prices[0] if len(prices) >= 1 else None
        total_price = prices[1] if len(prices) >= 2 else None

        products.append({
            "sku": sku,
            "product_name": product_name,
            "product_text": raw_product_text,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": total_price,
        })

    return products


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME)


def ingest_pdfs(force: bool = False) -> Dict:
    if not PDF_ROOT.exists():
        raise FileNotFoundError(f"PDF_ROOT nicht gefunden: {PDF_ROOT}")

    processed = load_processed_files()
    collection = get_collection()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    pdf_files = list(PDF_ROOT.rglob("*.pdf"))
    imported_products = 0
    imported_pdfs = 0
    skipped_pdfs = 0

    for pdf_path in pdf_files:
        current_hash = file_hash(pdf_path)
        pdf_key = str(pdf_path.relative_to(PDF_ROOT))

        if not force and processed.get(pdf_key) == current_hash:
            skipped_pdfs += 1
            continue

        # Bei force oder geänderter Datei alte Einträge für diese PDF löschen
        existing = collection.get(where={"source_pdf": pdf_key})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])

        pages = extract_text_by_page(pdf_path)
        offer_number = "unknown"
        pdf_product_count = 0

        for page_data in pages:
            page = page_data["page"]
            text = page_data["text"]
            if offer_number == "unknown":
                offer_number = extract_offer_number(text)

            product_lines = extract_product_lines(text)

            for idx, product in enumerate(product_lines, start=1):
                normalized = normalize_text(product["product_text"])
                if not normalized:
                    continue

                doc_id = hashlib.md5(f"{pdf_key}|{page}|{idx}|{product['sku']}".encode("utf-8")).hexdigest()
                embedding = model.encode(normalized).tolist()

                collection.upsert(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[normalized],
                    metadatas=[
                        {
                            "sku": product["sku"],
                            "product_name": product["product_name"],
                            "quantity": product["quantity"] if product["quantity"] is not None else "unknown",
                            "unit_price": product["unit_price"] if product["unit_price"] else "unknown",
                            "total_price": product["total_price"] if product["total_price"] else "unknown",
                            "source_pdf": pdf_key,
                            "filename": pdf_path.name,
                            "page": page,
                            "offer_number": offer_number,
                            "year_folder": pdf_path.parent.name,
                        }
                    ],
                )
                imported_products += 1
                pdf_product_count += 1

        processed[pdf_key] = current_hash
        imported_pdfs += 1

    save_processed_files(processed)

    return {
        "pdf_root": str(PDF_ROOT),
        "total_pdfs_found": len(pdf_files),
        "imported_pdfs": imported_pdfs,
        "skipped_pdfs": skipped_pdfs,
        "imported_products": imported_products,
    }


if __name__ == "__main__":
    print(ingest_pdfs())
