from typing import Dict, List

import requests

from config import OLLAMA_MODEL, OLLAMA_URL


def build_context(results: List[Dict]) -> str:
    if not results:
        return "Keine Treffer gefunden."

    lines = []
    for idx, r in enumerate(results, start=1):
        lines.append(
            f"Treffer {idx}:\n"
            f"SKU: {r.get('sku')}\n"
            f"Menge: {r.get('quantity')}\n"
            f"Angebot: {r.get('offer_number')}\n"
            f"Quelle PDF: {r.get('source_pdf')}\n"
            f"Seite: {r.get('page')}\n"
            f"Distance: {r.get('distance')}\n"
            f"Text: {r.get('matched_text')}\n"
        )
    return "\n".join(lines)


def ask_ollama(query: str, search_result: Dict) -> str:
    sold = search_result.get("sold", False)
    context = build_context(search_result.get("results", []))

    system_prompt = f"""
You are a sales assistant for Example Company Ltd.

IMPORTANT:
The system has already found valid matches in the database.
Therefore, you should answer that YES, a sold or quoted product was found.

Answer only based on the provided sources.
Do not invent products.
Mention the SKU, product name, offer number, date, and PDF if available.

Always state in which PDF the information was found, including the PDF file name.

Answer in English, briefly and clearly.

User question:
{query}

Found sources:
{context}
""".strip()

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "No se pudo generar una respuesta.")
    except requests.RequestException as exc:
        return (
            "No se pudo conectar con Ollama. Verifica que Ollama esté instalado y ejecutándose "
            f"con el modelo '{OLLAMA_MODEL}'. Error: {exc}"
        )
