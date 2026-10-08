"""v1 pricing (pre-plugin). Not imported anywhere; kept for the audit trail."""
from decimal import Decimal

from .utils import TAX_TABLE, money


def price_v1(order):
    sub = sum(Decimal(str(p)) * q for _, q, p in order["items"])
    if order.get("promo_code") == "SAVE10":
        sub *= Decimal("0.9")
    if order.get("loyalty_years"):
        sub *= 1 - Decimal(min(order["loyalty_years"], 10)) / 100  # stacks with promo
    ship = Decimal("0") if sub > 150 else Decimal("5.00")
    tax = (sub + ship) * Decimal(str(TAX_TABLE[order["region"]]))
    return money(sub + ship + tax)
