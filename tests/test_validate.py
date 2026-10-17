from decimal import Decimal

from extractor.models import ExtractedDocument, LineItem
from extractor.validate import validate_batch, validate_document


def _item(description="Widget", qty="2", price="10.00", vat="0.20", total="20.00") -> LineItem:
    return LineItem(
        description=description,
        quantity=Decimal(qty),
        unit_price=Decimal(price),
        vat_rate=Decimal(vat),
        line_total=Decimal(total),
    )


def _doc(**overrides) -> ExtractedDocument:
    base = dict(
        source_filename="a.pdf",
        doc_type="invoice",
        supplier="Nordik Office Supplies AB",
        document_number="INV-1",
        po_number="PO-1",
        currency="EUR",
        line_items=[_item()],
        subtotal=Decimal("20.00"),
        vat_amount=Decimal("4.00"),
        total=Decimal("24.00"),
    )
    base.update(overrides)
    return ExtractedDocument(**base)


def test_clean_document_has_no_issues():
    assert validate_document(_doc()) == []


def test_line_items_must_sum_to_subtotal():
    issues = validate_document(_doc(subtotal=Decimal("50.00"), vat_amount=Decimal("10.00"), total=Decimal("60.00")))
    codes = {issue.code for issue in issues}
    assert "line_sum_mismatch" in codes
    assert any("20.00" in issue.message and "50.00" in issue.message for issue in issues)


def test_vat_is_checked_against_line_rates():
    issues = validate_document(_doc(vat_amount=Decimal("1.00"), total=Decimal("21.00")))
    assert any(issue.code == "vat_mismatch" for issue in issues)
    assert any("1.00" in issue.message and "4.00" in issue.message for issue in issues)


def test_total_must_equal_subtotal_plus_vat():
    issues = validate_document(_doc(total=Decimal("99.00")))
    assert any(issue.code == "total_mismatch" for issue in issues)


def test_missing_po_is_a_warning():
    issues = validate_document(_doc(po_number=None))
    assert len(issues) == 1
    assert issues[0].code == "missing_po"
    assert issues[0].severity == "warning"


def test_duplicate_invoice_numbers_in_a_batch():
    first = _doc(source_filename="one.pdf")
    second = _doc(source_filename="two.pdf", subtotal=Decimal("20.00"))
    reviewed = validate_batch([first, second])
    assert all(any(issue.code == "duplicate_invoice" for issue in row.issues) for row in reviewed)
    assert "one.pdf" in reviewed[0].issues[-1].message
    assert "two.pdf" in reviewed[0].issues[-1].message


def test_same_number_from_different_suppliers_is_not_a_duplicate():
    first = _doc(supplier="Nordik Office Supplies AB")
    second = _doc(supplier="Baltic Packaging Oy", source_filename="other.pdf")
    reviewed = validate_batch([first, second])
    assert not any(issue.code == "duplicate_invoice" for row in reviewed for issue in row.issues)


def test_line_quantity_times_price():
    broken = _item(total="99.00")
    issues = validate_document(_doc(line_items=[broken], subtotal=Decimal("99.00"), vat_amount=Decimal("19.80"), total=Decimal("118.80")))
    assert any(issue.code == "line_math_mismatch" for issue in issues)
