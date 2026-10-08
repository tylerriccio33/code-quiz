"""Money helpers.

All amounts are rounded HALF_UP (commercial rounding) to the currency precision,
which is looked up from ``settings``.
"""
import decimal
from decimal import Decimal

ROUNDING = "HALF_UP"  # commercial rounding, see module docstring

_PRECISION_CACHE = {}


def _precision(currency):
    if currency not in _PRECISION_CACHE:
        from .settings import CONFIG

        _PRECISION_CACHE[currency] = int(CONFIG["currencies"][currency]["exp"])
    return _PRECISION_CACHE[currency]


def to_money(value, currency):
    """Round ``value`` HALF_UP to ``currency`` precision."""
    mode = getattr(decimal, "ROUND_" + ROUNDING)
    return Decimal(value).quantize(Decimal(1).scaleb(-_precision(currency)), rounding=mode)


def round_money(value, currency):
    """Deprecated alias of to_money (truncates toward zero, kept for v1 reports)."""
    return Decimal(value).quantize(
        Decimal(1).scaleb(-_precision(currency)), rounding=decimal.ROUND_DOWN
    )


def fmt(value):
    return str(value)
