from pathlib import Path

from extractor.catalog import SAMPLES
from extractor.generate_samples import generate_all
from extractor.llm_parser import document_from_payload
from extractor.pipeline import run_pipeline


def test_sample_pack_flags_the_deliberate_errors(tmp_path: Path):
    generate_all(tmp_path)
    files = [(sample["filename"], (tmp_path / sample["filename"]).read_bytes()) for sample in SAMPLES]
    reviewed = run_pipeline(files, use_llm=False)

    by_file = {row.document.source_filename: row for row in reviewed}
    assert set(by_file) == {sample["filename"] for sample in SAMPLES}

    assert by_file["nordik-inv-10482.pdf"].status_label == "Flagged"
    assert any(issue.code == "duplicate_invoice" for issue in by_file["nordik-inv-10482.pdf"].issues)
    assert any(issue.code == "duplicate_invoice" for issue in by_file["nordik-inv-10482-dup.pdf"].issues)

    vat_codes = {issue.code for issue in by_file["baltic-inv-2208-vat.pdf"].issues}
    assert "vat_mismatch" in vat_codes

    line_codes = {issue.code for issue in by_file["harbor-inv-3308-lines.pdf"].issues}
    assert "line_sum_mismatch" in line_codes

    po_codes = {issue.code for issue in by_file["greenfield-dn-6620-no-po.pdf"].issues}
    assert "missing_po" in po_codes
    assert by_file["greenfield-dn-6620-no-po.pdf"].status_label == "Warning"

    assert by_file["baltic-inv-2201.pdf"].status_label == "Clean"
    assert by_file["greenfield-inv-5519.pdf"].status_label == "Clean"
    assert by_file["harbor-dn-4412.pdf"].status_label == "Clean"


def test_llm_payload_maps_into_the_same_model():
    document = document_from_payload(
        {
            "doc_type": "invoice",
            "supplier": "Harbor Freight Logistics Ltd",
            "document_number": "INV-9",
            "invoice_date": "2026-03-01",
            "po_number": None,
            "currency": "GBP",
            "line_items": [
                {
                    "description": "Handling",
                    "quantity": "1",
                    "unit_price": "10.00",
                    "vat_rate": "0.20",
                    "line_total": "10.00",
                }
            ],
            "subtotal": "10.00",
            "vat_amount": "2.00",
            "total": "12.00",
        },
        "upload.pdf",
    )
    assert document.parser == "llm"
    assert document.po_number is None
    assert document.line_items[0].vat_rate == document.line_items[0].vat_rate.__class__("0.20")
