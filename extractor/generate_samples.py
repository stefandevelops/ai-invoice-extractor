"""Render the bundled fictional invoices and delivery notes to PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
    KeepTogether,
    HRFlowable,
)

from extractor.catalog import BUYER, SAMPLES, SUPPLIERS
from extractor.money import money

INK = colors.HexColor("#1C2428")
TEAL = colors.HexColor("#1F4E5F")
TEAL_SOFT = colors.HexColor("#D7E3E6")
PAPER = colors.HexColor("#F7F5F0")
RULE = colors.HexColor("#C9C2B4")
MUTED = colors.HexColor("#5C656A")
ROW_ALT = colors.HexColor("#F3EFE6")
WHITE = colors.white

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "company": ParagraphStyle(
            "company",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=WHITE,
            leading=16,
        ),
        "company_meta": ParagraphStyle(
            "company_meta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=WHITE,
            leading=11,
        ),
        "doc_kind": ParagraphStyle(
            "doc_kind",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=WHITE,
            alignment=TA_RIGHT,
            leading=20,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leading=10,
        ),
        "value": ParagraphStyle(
            "value",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=INK,
            leading=13,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=INK,
            leading=12,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=INK,
            leading=12,
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=WHITE,
            leading=10,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=INK,
            leading=11,
        ),
        "table_cell_right": ParagraphStyle(
            "table_cell_right",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=INK,
            alignment=TA_RIGHT,
            leading=11,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            textColor=MUTED,
            leading=10,
            alignment=TA_LEFT,
        ),
        "extract": ParagraphStyle(
            "extract",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=6.5,
            textColor=MUTED,
            leading=8.2,
        ),
    }


def _format_display_date(iso_date: str | None) -> str:
    if not iso_date:
        return "—"
    year, month, day = iso_date.split("-")
    months = (
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    )
    return f"{int(day)} {months[int(month) - 1]} {year}"


def _header(sample: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    supplier = SUPPLIERS[sample["supplier_key"]]
    kind = "INVOICE" if sample["doc_type"] == "invoice" else "DELIVERY NOTE"
    left = [
        Paragraph(supplier["name"], styles["company"]),
        Paragraph("<br/>".join(supplier["address"]), styles["company_meta"]),
        Paragraph(f"VAT {supplier['vat']}  ·  {supplier['email']}", styles["company_meta"]),
    ]
    right = [Paragraph(kind, styles["doc_kind"]), Paragraph("Fictional sample", styles["company_meta"])]
    table = Table([[left, right]], colWidths=[120 * mm, 70 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TEAL),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _meta_block(sample: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    fields: list[tuple[str, str]] = []
    if sample["doc_type"] == "invoice":
        fields.append(("Invoice number", sample["document_number"]))
        fields.append(("Invoice date", _format_display_date(sample.get("invoice_date"))))
        fields.append(("Due date", _format_display_date(sample.get("due_date"))))
    else:
        fields.append(("Delivery note", sample["document_number"]))
        fields.append(("Delivery date", _format_display_date(sample.get("delivery_date"))))
    fields.append(("PO number", sample.get("po_number") or "—"))
    fields.append(("Currency", sample["currency"]))

    cells = []
    for label, value in fields:
        cells.append(
            [
                Paragraph(label.upper(), styles["label"]),
                Paragraph(value, styles["value"]),
            ]
        )
    table = Table(cells, colWidths=[40 * mm, 50 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TEAL_SOFT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.4, TEAL),
            ]
        )
    )
    return table


def _party_block(styles: dict[str, ParagraphStyle]) -> list:
    lines = [Paragraph("BILL TO / DELIVER TO", styles["label"]), Paragraph(BUYER["name"], styles["body_bold"])]
    for line in BUYER["address"]:
        lines.append(Paragraph(line, styles["body"]))
    return lines


def _line_table(sample: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    header = [
        Paragraph("Description", styles["table_head"]),
        Paragraph("Qty", styles["table_head"]),
        Paragraph("Unit price", styles["table_head"]),
        Paragraph("VAT", styles["table_head"]),
        Paragraph("Amount", styles["table_head"]),
    ]
    rows = [header]
    for item in sample["line_items"]:
        vat_pct = f"{money(item['vat_rate']) * 100:.0f}%"
        rows.append(
            [
                Paragraph(item["description"], styles["table_cell"]),
                Paragraph(item["quantity"], styles["table_cell_right"]),
                Paragraph(f"{money(item['unit_price']):,.2f}", styles["table_cell_right"]),
                Paragraph(vat_pct, styles["table_cell_right"]),
                Paragraph(f"{money(item['line_total']):,.2f}", styles["table_cell_right"]),
            ]
        )
    table = Table(rows, colWidths=[88 * mm, 18 * mm, 28 * mm, 18 * mm, 28 * mm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
        ("BOX", (0, 0), (-1, -1), 0.4, TEAL),
    ]
    for index in range(1, len(rows)):
        if index % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, index), (-1, index), ROW_ALT))
    table.setStyle(TableStyle(style_cmds))
    return table


def _totals(sample: dict[str, Any], styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [Paragraph("Subtotal (ex VAT)", styles["body"]), Paragraph(f"{money(sample['subtotal']):,.2f}", styles["body"])],
        [Paragraph("VAT", styles["body"]), Paragraph(f"{money(sample['vat_amount']):,.2f}", styles["body"])],
        [Paragraph("Total", styles["body_bold"]), Paragraph(f"{money(sample['total']):,.2f} {sample['currency']}", styles["body_bold"])],
    ]
    table = Table(rows, colWidths=[40 * mm, 35 * mm])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, -1), (-1, -1), 0.8, TEAL),
                ("TOPPADDING", (0, -1), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def extract_block(sample: dict[str, Any]) -> str:
    """Stable key=value payload the demo parser reads from the PDF text layer."""
    lines = [
        "BEGIN_EXTRACT",
        f"doc_type={sample['doc_type']}",
        f"supplier={SUPPLIERS[sample['supplier_key']]['name']}",
        f"document_number={sample['document_number']}",
        f"invoice_date={sample.get('invoice_date') or ''}",
        f"due_date={sample.get('due_date') or ''}",
        f"delivery_date={sample.get('delivery_date') or ''}",
        f"po_number={sample.get('po_number') or ''}",
        f"currency={sample['currency']}",
        f"subtotal={sample['subtotal']}",
        f"vat_amount={sample['vat_amount']}",
        f"total={sample['total']}",
    ]
    for item in sample["line_items"]:
        lines.append(
            "LINE|{description}|{quantity}|{unit_price}|{vat_rate}|{line_total}".format(**item)
        )
    lines.append("END_EXTRACT")
    return "\n".join(lines)


def _draw_background(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()


def build_pdf(sample: dict[str, Any], output_path: Path) -> None:
    styles = _styles()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{sample['document_number']} — fictional sample",
        author="Document Extractor demo",
    )
    supplier = SUPPLIERS[sample["supplier_key"]]
    story: list = [
        _header(sample, styles),
        Spacer(1, 8 * mm),
        Table(
            [[_party_block(styles), _meta_block(sample, styles)]],
            colWidths=[95 * mm, 90 * mm],
        ),
        Spacer(1, 8 * mm),
        _line_table(sample, styles),
        Spacer(1, 6 * mm),
        Table([[Spacer(1, 1), _totals(sample, styles)]], colWidths=[115 * mm, 75 * mm]),
        Spacer(1, 6 * mm),
        HRFlowable(width="100%", thickness=0.4, color=RULE),
        Spacer(1, 3 * mm),
        Paragraph(
            f"Pay to {supplier['iban']} · Quote {sample['document_number']} on the transfer. "
            "This PDF is a fictional sample built for a portfolio demo. "
            "It is not a real commercial document and must not be used for payment.",
            styles["footer"],
        ),
        Spacer(1, 5 * mm),
        KeepTogether(
            [
                Paragraph("STRUCTURED EXTRACT (demo parser)", styles["label"]),
                Spacer(1, 1 * mm),
                Paragraph(extract_block(sample).replace("\n", "<br/>"), styles["extract"]),
            ]
        ),
    ]
    doc.build(story, onFirstPage=_draw_background, onLaterPages=_draw_background)


def generate_all(output_dir: Path | None = None) -> list[Path]:
    target = output_dir or SAMPLES_DIR
    written = []
    for sample in SAMPLES:
        path = target / sample["filename"]
        build_pdf(sample, path)
        written.append(path)
    return written


if __name__ == "__main__":
    paths = generate_all()
    for path in paths:
        print(path)
