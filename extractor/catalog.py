"""Canonical fake documents used to generate sample PDFs and drive demo mode.

Every company, VAT number, IBAN and address here is invented.
"""

from __future__ import annotations

from typing import Any

BUYER = {
    "name": "Northshore Trading Ltd",
    "address": ["18 Harbour Walk", "Edinburgh EH6 6DN", "United Kingdom"],
}

SUPPLIERS: dict[str, dict[str, Any]] = {
    "nordik": {
        "name": "Nordik Office Supplies AB",
        "address": ["Kungsgatan 12", "111 35 Stockholm", "Sweden"],
        "vat": "SE556123456701",
        "iban": "SE00 FAKE 0000 0000 0000",
        "email": "accounts@nordik-office.example",
    },
    "baltic": {
        "name": "Baltic Packaging Oy",
        "address": ["Teollisuuskatu 8", "00510 Helsinki", "Finland"],
        "vat": "FI24781235",
        "iban": "FI00 FAKE 0000 0000 00",
        "email": "billing@baltic-pack.example",
    },
    "harbor": {
        "name": "Harbor Freight Logistics Ltd",
        "address": ["22 Basin Road", "Felixstowe IP11 2AX", "United Kingdom"],
        "vat": "GB844193017",
        "iban": "GB00 FAKE 0000 0000 00",
        "email": "finance@harbor-freight.example",
    },
    "greenfield": {
        "name": "Greenfield Coffee Roasters Ltd",
        "address": ["Unit 4, Marina Business Park", "Cork T12 XY99", "Ireland"],
        "vat": "IE6439281Q",
        "iban": "IE00 FAKE 0000 0000 00",
        "email": "accounts@greenfield-coffee.example",
    },
}


def _line(description: str, qty: str, unit_price: str, vat_rate: str, line_total: str) -> dict[str, str]:
    return {
        "description": description,
        "quantity": qty,
        "unit_price": unit_price,
        "vat_rate": vat_rate,
        "line_total": line_total,
    }


SAMPLES: list[dict[str, Any]] = [
    {
        "filename": "nordik-inv-10482.pdf",
        "supplier_key": "nordik",
        "doc_type": "invoice",
        "document_number": "INV-10482",
        "invoice_date": "2026-03-12",
        "due_date": "2026-04-11",
        "po_number": "PO-88421",
        "currency": "EUR",
        "subtotal": "1140.00",
        "vat_amount": "285.00",
        "total": "1425.00",
        "intended_issues": [],
        "notes": "Standard office-supplies invoice. Totals are consistent.",
        "line_items": [
            _line("Copy paper A4 80gsm (box of 5)", "8", "42.50", "0.25", "340.00"),
            _line("Toner cartridge HP 59A", "4", "78.00", "0.25", "312.00"),
            _line("Desk stapler heavy-duty", "12", "14.50", "0.25", "174.00"),
            _line("Archive boxes (pack of 10)", "6", "19.00", "0.25", "114.00"),
            _line("Whiteboard markers (pack of 8)", "15", "6.80", "0.25", "102.00"),
            _line("Cable ties 200mm (bag of 100)", "20", "4.90", "0.25", "98.00"),
        ],
    },
    {
        "filename": "baltic-inv-2201.pdf",
        "supplier_key": "baltic",
        "doc_type": "invoice",
        "document_number": "INV-2201",
        "invoice_date": "2026-02-28",
        "due_date": "2026-03-30",
        "po_number": "PO-77109",
        "currency": "EUR",
        "subtotal": "756.60",
        "vat_amount": "181.58",
        "total": "938.18",
        "intended_issues": [],
        "notes": "Finnish packaging supplier. 24% VAT, totals consistent.",
        "line_items": [
            _line("Double-wall carton 400x300x250", "200", "1.85", "0.24", "370.00"),
            _line("Kraft void fill 50m roll", "24", "8.40", "0.24", "201.60"),
            _line("Pallet wrap 20 micron", "10", "18.50", "0.24", "185.00"),
        ],
    },
    {
        "filename": "greenfield-inv-5519.pdf",
        "supplier_key": "greenfield",
        "doc_type": "invoice",
        "document_number": "INV-5519",
        "invoice_date": "2026-03-01",
        "due_date": "2026-03-31",
        "po_number": "PO-66218",
        "currency": "EUR",
        "subtotal": "3616.00",
        "vat_amount": "831.68",
        "total": "4447.68",
        "intended_issues": [],
        "notes": "Coffee roast invoice. 23% Irish VAT, totals consistent.",
        "line_items": [
            _line("Ethiopia Guji G1 60kg bag", "4", "412.00", "0.23", "1648.00"),
            _line("Brazil Cerrado 60kg bag", "6", "298.00", "0.23", "1788.00"),
            _line("Paper filters 90mm (case)", "8", "22.50", "0.23", "180.00"),
        ],
    },
    {
        "filename": "harbor-dn-4412.pdf",
        "supplier_key": "harbor",
        "doc_type": "delivery_note",
        "document_number": "DN-4412",
        "delivery_date": "2026-03-15",
        "po_number": "PO-90331",
        "currency": "GBP",
        "subtotal": "270.00",
        "vat_amount": "54.00",
        "total": "324.00",
        "intended_issues": [],
        "notes": "Delivery note with a PO and consistent handling charges.",
        "line_items": [
            _line("Outbound handling (per pallet)", "6", "38.00", "0.20", "228.00"),
            _line("Fuel surcharge", "1", "42.00", "0.20", "42.00"),
        ],
    },
    {
        "filename": "nordik-inv-10482-dup.pdf",
        "supplier_key": "nordik",
        "doc_type": "invoice",
        "document_number": "INV-10482",
        "invoice_date": "2026-03-18",
        "due_date": "2026-04-17",
        "po_number": "PO-88421",
        "currency": "EUR",
        "subtotal": "370.00",
        "vat_amount": "92.50",
        "total": "462.50",
        "intended_issues": ["duplicate_invoice"],
        "notes": "Same invoice number as nordik-inv-10482.pdf, sent again a week later.",
        "line_items": [
            _line("Monitor arm dual", "2", "89.00", "0.25", "178.00"),
            _line("USB-C dock", "3", "64.00", "0.25", "192.00"),
        ],
    },
    {
        "filename": "baltic-inv-2208-vat.pdf",
        "supplier_key": "baltic",
        "doc_type": "invoice",
        "document_number": "INV-2208",
        "invoice_date": "2026-03-08",
        "due_date": "2026-04-07",
        "po_number": "PO-77144",
        "currency": "EUR",
        "subtotal": "404.00",
        "vat_amount": "40.40",
        "total": "444.40",
        "intended_issues": ["vat_mismatch"],
        "notes": "Printed VAT is 10% of the subtotal; line items are at 24%.",
        "line_items": [
            _line("Corrugated trays 600x400", "100", "3.20", "0.24", "320.00"),
            _line("Packing tape 48mm", "40", "2.10", "0.24", "84.00"),
        ],
    },
    {
        "filename": "harbor-inv-3308-lines.pdf",
        "supplier_key": "harbor",
        "doc_type": "invoice",
        "document_number": "INV-3308",
        "invoice_date": "2026-03-10",
        "due_date": "2026-04-09",
        "po_number": "PO-90388",
        "currency": "GBP",
        "subtotal": "750.00",
        "vat_amount": "150.00",
        "total": "900.00",
        "intended_issues": ["line_sum_mismatch"],
        "notes": "Line items add to 626.00; the printed subtotal is 750.00.",
        "line_items": [
            _line("Cross-dock handling", "12", "45.00", "0.20", "540.00"),
            _line("Fuel surcharge", "1", "86.00", "0.20", "86.00"),
        ],
    },
    {
        "filename": "greenfield-dn-6620-no-po.pdf",
        "supplier_key": "greenfield",
        "doc_type": "delivery_note",
        "document_number": "DN-6620",
        "delivery_date": "2026-03-20",
        "po_number": None,
        "currency": "EUR",
        "subtotal": "712.00",
        "vat_amount": "163.76",
        "total": "875.76",
        "intended_issues": ["missing_po"],
        "notes": "Delivery note with no purchase order number.",
        "line_items": [
            _line("Colombia Supremo 60kg bag", "2", "356.00", "0.23", "712.00"),
        ],
    },
]


def sample_by_filename(filename: str) -> dict[str, Any] | None:
    for sample in SAMPLES:
        if sample["filename"] == filename:
            return sample
    return None


def sample_by_document_number(document_number: str) -> list[dict[str, Any]]:
    return [sample for sample in SAMPLES if sample["document_number"] == document_number]


def bundled_sample_filenames() -> list[str]:
    return [sample["filename"] for sample in SAMPLES]
