from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

TWOPLACE = Decimal("0.01")


def to_decimal(value: Any) -> Decimal:
    """Parse a number or numeric string into a 2-decimal Decimal."""
    if isinstance(value, Decimal):
        return value.quantize(TWOPLACE, rounding=ROUND_HALF_UP)
    if value is None or value == "":
        raise InvalidOperation("empty amount")
    text = str(value).strip()
    for token in ("EUR", "GBP", "USD", "SEK", "€", "£", "$"):
        text = text.replace(token, "")
    text = text.strip().replace(" ", "")
    if text.count(",") == 1 and text.count(".") == 0:
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")
    return Decimal(text).quantize(TWOPLACE, rounding=ROUND_HALF_UP)


def money(value: Any) -> Decimal:
    return to_decimal(value)


def fmt_money(value: Decimal | None, currency: str | None = None) -> str:
    if value is None:
        return "—"
    formatted = f"{value:,.2f}"
    if currency:
        return f"{formatted} {currency}"
    return formatted


def nearly_equal(left: Decimal, right: Decimal, tolerance: Decimal = Decimal("0.02")) -> bool:
    return abs(left - right) <= tolerance
