from pathlib import Path

from extractor.catalog import SAMPLES
from extractor.demo_parser import parse_demo, parse_generic
from extractor.generate_samples import extract_block, generate_all
from extractor.pdf_text import extract_text


def test_extract_block_round_trip():
    sample = SAMPLES[0]
    parsed = parse_demo(extract_block(sample), sample["filename"])
    assert parsed.document_number == "INV-10482"
    assert parsed.supplier == "Nordik Office Supplies AB"
    assert parsed.po_number == "PO-88421"
    assert len(parsed.line_items) == 6
    assert parsed.parser == "demo"


def test_generated_pdfs_are_readable(tmp_path: Path):
    generate_all(tmp_path)
    sample = next(item for item in SAMPLES if item["filename"] == "baltic-inv-2208-vat.pdf")
    text = extract_text((tmp_path / sample["filename"]).read_bytes())
    parsed = parse_demo(text, sample["filename"])
    assert parsed.document_number == "INV-2208"
    assert parsed.vat_amount == sample["vat_amount"] or str(parsed.vat_amount) == sample["vat_amount"]
    assert str(parsed.vat_amount) == "40.40"
    assert parsed.po_number == "PO-77144"


def test_missing_po_sample_parses_as_empty(tmp_path: Path):
    generate_all(tmp_path)
    path = tmp_path / "greenfield-dn-6620-no-po.pdf"
    parsed = parse_demo(extract_text(path.read_bytes()), path.name)
    assert parsed.doc_type == "delivery_note"
    assert parsed.po_number is None
    assert parsed.document_number == "DN-6620"


def test_generic_parser_reads_labels():
    text = """
    Baltic Packaging Oy
    INVOICE
    Invoice number: INV-9999
    Invoice date: 12 Mar 2026
    PO number: PO-11111
    Currency: EUR
    Subtotal (ex VAT)  100.00
    VAT  24.00
    Total  124.00
    """
    parsed = parse_generic(text, "manual.pdf")
    assert parsed.document_number == "INV-9999"
    assert parsed.po_number == "PO-11111"
    assert parsed.parser == "generic"
