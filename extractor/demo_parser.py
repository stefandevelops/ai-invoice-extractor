"""Deterministic parsers used when no LLM key is set.

Bundled samples include a BEGIN_EXTRACT / END_EXTRACT block so demo mode
is stable. Unknown PDFs fall back to a small label-scraping parser.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

from dateutil import parser as date_parser

from extractor.models import ExtractedDocument, LineItem
from extractor.money import money

EXTRACT_RE = re.compile(r"BEGIN_EXTRACT\s*(.*?)\s*END_EXTRACT", re.DOTALL | re.IGNORECASE)


def parse_demo(text: str, filename: str) -> ExtractedDocument:
    extracted = _parse_extract_block(text, filename)
    if extracted is not None:
        extracted.parser = "demo"
        return extracted
    generic = parse_generic(text, filename)
    generic.parser = "generic"
    return generic


def _parse_extract_block(text: str, filename: str) -> ExtractedDocument | None:
    match = EXTRACT_RE.search(text)
    if not match:
        return None
    fields: dict[str, str] = {}
    lines: list[LineItem] = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("LINE|"):
            parts = line.split("|")
            if len(parts) != 6:
                continue
            _, description, quantity, unit_price, vat_rate, line_total = parts
            lines.append(
                LineItem(
                    description=description,
                    quantity=money(quantity),
                    unit_price=money(unit_price),
                    vat_rate=money(vat_rate),
                    line_total=money(line_total),
                )
            )
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()

    document_number = fields.get("document_number", "")
    if not document_number:
        return None

    doc_type = fields.get("doc_type", "invoice")
    if doc_type not in {"invoice", "delivery_note"}:
        doc_type = "invoice"

    return ExtractedDocument(
        source_filename=filename,
        doc_type=doc_type,  # type: ignore[arg-type]
        supplier=fields.get("supplier") or "Unknown supplier",
        document_number=document_number,
        invoice_date=_optional_date(fields.get("invoice_date")),
        due_date=_optional_date(fields.get("due_date")),
        delivery_date=_optional_date(fields.get("delivery_date")),
        po_number=fields.get("po_number") or None,
        currency=fields.get("currency") or "EUR",
        line_items=lines,
        subtotal=_optional_money(fields.get("subtotal")),
        vat_amount=_optional_money(fields.get("vat_amount")),
        total=_optional_money(fields.get("total")),
        parser="demo",
    )


LABEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("document_number", re.compile(r"(?:Invoice number|Delivery note)\s*[:#]?\s*([A-Z]{2,3}-\d+)", re.I)),
    ("po_number", re.compile(r"PO number\s*[:#]?\s*(PO-\d+)", re.I)),
    ("currency", re.compile(r"Currency\s*[:#]?\s*([A-Z]{3})", re.I)),
    ("invoice_date", re.compile(r"Invoice date\s*[:#]?\s*([0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", re.I)),
    ("due_date", re.compile(r"Due date\s*[:#]?\s*([0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", re.I)),
    ("delivery_date", re.compile(r"Delivery date\s*[:#]?\s*([0-9]{1,2}\s+[A-Za-z]{3}\s+[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2})", re.I)),
    ("subtotal", re.compile(r"Subtotal(?:\s*\(ex VAT\))?\s*[:#]?\s*([0-9,]+\.\d{2})", re.I)),
    ("vat_amount", re.compile(r"\bVAT\b(?!\s*%)\s*[:#]?\s*([0-9,]+\.\d{2})", re.I)),
    ("total", re.compile(r"\bTotal\b\s*[:#]?\s*([0-9,]+\.\d{2})", re.I)),
]


def parse_generic(text: str, filename: str) -> ExtractedDocument:
    found: dict[str, str] = {}
    for key, pattern in LABEL_PATTERNS:
        match = pattern.search(text)
        if match:
            found[key] = match.group(1).strip()

    doc_type: Literal["invoice", "delivery_note"] = "delivery_note" if re.search(r"delivery note", text, re.I) else "invoice"
    supplier = _guess_supplier(text)
    document_number = found.get("document_number") or "UNKNOWN"

    return ExtractedDocument(
        source_filename=filename,
        doc_type=doc_type,
        supplier=supplier,
        document_number=document_number,
        invoice_date=_optional_date(found.get("invoice_date")),
        due_date=_optional_date(found.get("due_date")),
        delivery_date=_optional_date(found.get("delivery_date")),
        po_number=found.get("po_number"),
        currency=found.get("currency") or "EUR",
        line_items=[],
        subtotal=_optional_money(found.get("subtotal")),
        vat_amount=_optional_money(found.get("vat_amount")),
        total=_optional_money(found.get("total")),
        parser="generic",
    )


def _guess_supplier(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if len(cleaned) >= 4 and not cleaned.upper().startswith(("INVOICE", "DELIVERY", "BILL", "PAGE")):
            return cleaned[:120]
    return "Unknown supplier"


def _optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date_parser.parse(value, dayfirst=False).date()
    except (ValueError, OverflowError, TypeError):
        return None


def _optional_money(value: str | None):
    if not value:
        return None
    try:
        return money(value)
    except Exception:
        return None
