from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal
    line_total: Decimal


class ExtractedDocument(BaseModel):
    source_filename: str
    doc_type: Literal["invoice", "delivery_note"]
    supplier: str
    document_number: str
    invoice_date: date | None = None
    due_date: date | None = None
    delivery_date: date | None = None
    po_number: str | None = None
    currency: str = "EUR"
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Decimal | None = None
    vat_amount: Decimal | None = None
    total: Decimal | None = None
    parser: Literal["demo", "llm", "generic"] = "demo"


class Issue(BaseModel):
    code: str
    severity: Literal["error", "warning"]
    message: str


class ReviewedDocument(BaseModel):
    document: ExtractedDocument
    issues: list[Issue] = Field(default_factory=list)

    @property
    def is_flagged(self) -> bool:
        return bool(self.issues)

    @property
    def status_label(self) -> str:
        if any(issue.severity == "error" for issue in self.issues):
            return "Flagged"
        if self.issues:
            return "Warning"
        return "Clean"
