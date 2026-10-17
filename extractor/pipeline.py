from __future__ import annotations

from pathlib import Path

from extractor.demo_parser import parse_demo
from extractor.llm_parser import llm_config_from_env, parse_with_llm
from extractor.models import ExtractedDocument, Issue, ReviewedDocument
from extractor.pdf_text import extract_text
from extractor.validate import validate_batch


def has_llm_credentials() -> bool:
    return llm_config_from_env() is not None


def run_pipeline(
    files: list[tuple[str, bytes]],
    use_llm: bool | None = None,
) -> list[ReviewedDocument]:
    """Extract and validate a batch of PDFs.

    `use_llm` defaults to True when an API key is present. Demo mode always
    uses the deterministic parser, which is reliable for the bundled samples.
    """
    if use_llm is None:
        use_llm = has_llm_credentials()

    extracted: list[ExtractedDocument] = []
    failures: list[ReviewedDocument] = []
    for filename, payload in files:
        try:
            extracted.append(extract_one(filename, payload, use_llm=use_llm))
        except Exception as exc:
            failures.append(
                ReviewedDocument(
                    document=ExtractedDocument(
                        source_filename=filename,
                        doc_type="invoice",
                        supplier="(unreadable)",
                        document_number="UNKNOWN",
                        parser="generic",
                    ),
                    issues=[
                        Issue(
                            code="extract_failed",
                            severity="error",
                            message=f"Could not extract this file: {exc}",
                        )
                    ],
                )
            )
    reviewed = validate_batch(extracted)
    return reviewed + failures


def extract_one(filename: str, pdf_bytes: bytes, use_llm: bool = False) -> ExtractedDocument:
    text = extract_text(pdf_bytes)
    if use_llm:
        return parse_with_llm(text, filename)
    return parse_demo(text, filename)


def load_bundled_samples(samples_dir: Path | None = None) -> list[tuple[str, bytes]]:
    from extractor.catalog import SAMPLES
    from extractor.generate_samples import generate_all

    folder = samples_dir or Path(__file__).resolve().parent.parent / "samples"
    if not folder.exists() or not any(folder.glob("*.pdf")):
        generate_all(folder)

    files = []
    for sample in SAMPLES:
        path = folder / sample["filename"]
        if path.exists():
            files.append((sample["filename"], path.read_bytes()))
    return files
