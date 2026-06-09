from typing import Dict, List

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_OUTPUT_TOKENS


def build_context(results: List[Dict]) -> str:
    if not results:
        return "No matches found."

    lines = []
    for idx, r in enumerate(results, start=1):
        lines.append(
            f"Match {idx}:\n"
            f"SKU: {r.get('sku')}\n"
            f"Product name: {r.get('product_name')}\n"
            f"Quantity: {r.get('quantity')}\n"
            f"Unit price: {r.get('unit_price')}\n"
            f"Total price: {r.get('total_price')}\n"
            f"Offer: {r.get('offer_number')}\n"
            f"PDF: {r.get('source_pdf')}\n"
            f"Page: {r.get('page')}\n"
            f"Distance: {r.get('distance')}\n"
            f"Text: {r.get('matched_text')}\n"
        )
    return "\n".join(lines)


def ask_llm(query: str, search_result: Dict) -> str:
    if not GEMINI_API_KEY:
        return "Gemini API key is missing. Please set GEMINI_API_KEY in the .env file."

    context = build_context(search_result.get("results", []))

    prompt = f"""
You are a sales search assistant for biotechnology and laboratory offers.

The system has already found valid matches in the database.
Answer only based on the provided sources.
Do not invent products, prices, quantities, PDFs, or SKUs.

If quantity, unit price, or total price are available, use the structured fields.
Always mention the PDF name.

User question:
{query}

Sources:
{context}
""".strip()

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            temperature=0.2,
        ),
    )

    return response.text or "No answer generated."