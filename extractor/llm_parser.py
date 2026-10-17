"""OpenAI-compatible extraction for arbitrary PDFs when an API key is set."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from extractor.models import ExtractedDocument, LineItem
from extractor.money import money

SCHEMA_HINT = """
Return only JSON (no markdown) with this shape:
{
  "doc_type": "invoice" | "delivery_note",
  "supplier": string,
  "document_number": string,
  "invoice_date": "YYYY-MM-DD" | null,
  "due_date": "YYYY-MM-DD" | null,
  "delivery_date": "YYYY-MM-DD" | null,
  "po_number": string | null,
  "currency": "EUR" | "GBP" | "USD" | string,
  "line_items": [
    {
      "description": string,
      "quantity": "0.00",
      "unit_price": "0.00",
      "vat_rate": "0.25",
      "line_total": "0.00"
    }
  ],
  "subtotal": "0.00" | null,
  "vat_amount": "0.00" | null,
  "total": "0.00" | null
}

Rules:
- vat_rate is a fraction (0.25 for 25%).
- Amounts are strings with two decimal places.
- If a field is not on the document, use null. Do not invent a PO number.
- document_number is the invoice or delivery-note number.
""".strip()


def llm_config_from_env() -> dict[str, str] | None:
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        return {
            "api_key": openai_key,
            "base_url": os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini",
            "provider": "openai",
        }

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return {
            "api_key": gemini_key,
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.0-flash",
            "provider": "gemini",
        }
    return None


def parse_with_llm(text: str, filename: str, client: Any | None = None, model: str | None = None) -> ExtractedDocument:
    config = llm_config_from_env()
    if client is None:
        if config is None:
            raise RuntimeError("No LLM credentials set")
        client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
        model = model or config["model"]
    if not model:
        model = (config or {}).get("model") or "gpt-4o-mini"

    snippet = text[:12000] if text else "(no extractable text — the PDF may be a scan)"
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You extract structured fields from invoices and delivery notes. " + SCHEMA_HINT,
            },
            {
                "role": "user",
                "content": f"Filename: {filename}\n\nDocument text:\n{snippet}",
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    payload = _load_json(raw)
    return document_from_payload(payload, filename, parser="llm")


def document_from_payload(payload: dict[str, Any], filename: str, parser: str = "llm") -> ExtractedDocument:
    doc_type = payload.get("doc_type") or "invoice"
    if doc_type not in {"invoice", "delivery_note"}:
        doc_type = "invoice"

    items = []
    for raw in payload.get("line_items") or []:
        try:
            items.append(
                LineItem(
                    description=str(raw.get("description") or "").strip() or "Line item",
                    quantity=money(raw.get("quantity") or 0),
                    unit_price=money(raw.get("unit_price") or 0),
                    vat_rate=money(raw.get("vat_rate") or 0),
                    line_total=money(raw.get("line_total") or 0),
                )
            )
        except Exception:
            continue

    return ExtractedDocument(
        source_filename=filename,
        doc_type=doc_type,
        supplier=str(payload.get("supplier") or "Unknown supplier"),
        document_number=str(payload.get("document_number") or "UNKNOWN"),
        invoice_date=_date_or_none(payload.get("invoice_date")),
        due_date=_date_or_none(payload.get("due_date")),
        delivery_date=_date_or_none(payload.get("delivery_date")),
        po_number=_blank_to_none(payload.get("po_number")),
        currency=str(payload.get("currency") or "EUR"),
        line_items=items,
        subtotal=_money_or_none(payload.get("subtotal")),
        vat_amount=_money_or_none(payload.get("vat_amount")),
        total=_money_or_none(payload.get("total")),
        parser=parser,  # type: ignore[arg-type]
    )


def _load_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re_unfence(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise
        data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("LLM response was not a JSON object")
    return data


def re_unfence(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)


def _blank_to_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_or_none(value: Any):
    if not value:
        return None
    from extractor.demo_parser import _optional_date

    return _optional_date(str(value))


def _money_or_none(value: Any):
    if value in (None, ""):
        return None
    try:
        return money(value)
    except Exception:
        return None
