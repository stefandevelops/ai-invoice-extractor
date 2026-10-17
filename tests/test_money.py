from decimal import Decimal

from extractor.money import money, nearly_equal


def test_parses_thousands_separators():
    assert money("1,140.00") == Decimal("1140.00")


def test_parses_european_comma_decimals():
    assert money("181,58") == Decimal("181.58")


def test_near_equality_allows_a_cent():
    assert nearly_equal(Decimal("10.00"), Decimal("10.01"))
    assert not nearly_equal(Decimal("10.00"), Decimal("10.05"))
