"""Currency rounding."""
from decimal import Decimal

from .constants import CURRENCY_DECIMALS, ROUNDING_MODE


def round_money(amount: Decimal, currency: str) -> Decimal:
    """Round to the currency's minor unit with banker's rounding (ROUND_HALF_EVEN)."""
    places = CURRENCY_DECIMALS[currency]
    return amount.quantize(Decimal(1).scaleb(-places), rounding=ROUNDING_MODE)
