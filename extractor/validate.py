from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from extractor.models import ExtractedDocument, Issue, ReviewedDocument
from extractor.money import fmt_money, nearly_equal


def validate_batch(documents: list[ExtractedDocument]) -> list[ReviewedDocument]:
    """Run per-document checks, then batch-level duplicate invoice detection."""
    reviewed = [ReviewedDocument(document=doc, issues=validate_document(doc)) for doc in documents]
    _flag_duplicates(reviewed)
    return reviewed


def validate_document(document: ExtractedDocument) -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(_line_sum_issues(document))
    issues.extend(_vat_issues(document))
    issues.extend(_total_issues(document))
    issues.extend(_missing_po_issues(document))
    issues.extend(_line_math_issues(document))
    return issues


def _line_sum_issues(document: ExtractedDocument) -> list[Issue]:
    if not document.line_items or document.subtotal is None:
        return []
    summed = sum((item.line_total for item in document.line_items), Decimal("0.00"))
    if nearly_equal(summed, document.subtotal):
        return []
    return [
        Issue(
            code="line_sum_mismatch",
            severity="error",
            message=(
                f"Line items add up to {fmt_money(summed, document.currency)} but the "
                f"printed subtotal is {fmt_money(document.subtotal, document.currency)}."
            ),
        )
    ]


def _vat_issues(document: ExtractedDocument) -> list[Issue]:
    if not document.line_items or document.vat_amount is None:
        return []
    expected = sum(
        (item.line_total * item.vat_rate for item in document.line_items),
        Decimal("0.00"),
    )
    expected = expected.quantize(Decimal("0.01"))
    if nearly_equal(expected, document.vat_amount):
        return []
    return [
        Issue(
            code="vat_mismatch",
            severity="error",
            message=(
                f"VAT is {fmt_money(document.vat_amount, document.currency)}; "
                f"line items at their stated rates come to {fmt_money(expected, document.currency)}."
            ),
        )
    ]


def _total_issues(document: ExtractedDocument) -> list[Issue]:
    if document.subtotal is None or document.vat_amount is None or document.total is None:
        return []
    expected = (document.subtotal + document.vat_amount).quantize(Decimal("0.01"))
    if nearly_equal(expected, document.total):
        return []
    return [
        Issue(
            code="total_mismatch",
            severity="error",
            message=(
                f"Subtotal plus VAT is {fmt_money(expected, document.currency)} "
                f"but the printed total is {fmt_money(document.total, document.currency)}."
            ),
        )
    ]


def _missing_po_issues(document: ExtractedDocument) -> list[Issue]:
    if document.po_number:
        return []
    kind = "invoice" if document.doc_type == "invoice" else "delivery note"
    return [
        Issue(
            code="missing_po",
            severity="warning",
            message=f"No purchase order number on this {kind}. Most AP teams need a PO before they can match or pay.",
        )
    ]


def _line_math_issues(document: ExtractedDocument) -> list[Issue]:
    issues = []
    for item in document.line_items:
        expected = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        if nearly_equal(expected, item.line_total):
            continue
        issues.append(
            Issue(
                code="line_math_mismatch",
                severity="error",
                message=(
                    f"'{item.description}': {item.quantity} × {fmt_money(item.unit_price)} "
                    f"is {fmt_money(expected)}, but the line total is {fmt_money(item.line_total)}."
                ),
            )
        )
    return issues


def _flag_duplicates(reviewed: list[ReviewedDocument]) -> None:
    grouped: dict[tuple[str, str], list[ReviewedDocument]] = defaultdict(list)
    for row in reviewed:
        number = row.document.document_number.strip().upper()
        if not number or number == "UNKNOWN":
            continue
        grouped[(row.document.supplier.strip().upper(), number)].append(row)

    for (_supplier, number), rows in grouped.items():
        if len(rows) < 2:
            continue
        names = ", ".join(row.document.source_filename for row in rows)
        for row in rows:
            row.issues.append(
                Issue(
                    code="duplicate_invoice",
                    severity="error",
                    message=(
                        f"Document number {number} appears on {len(rows)} files in this batch "
                        f"({names})."
                    ),
                )
            )
