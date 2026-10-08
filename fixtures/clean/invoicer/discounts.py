"""Discount rules.

Order of application:
1. Bulk line discount: each line with qty >= BULK_MIN_QTY gets BULK_RATE off.
2. Wholesale discount: WHOLESALE_RATE off the goods after bulk discounts.
3. Promo code OR loyalty (never both): whichever saves more on the amount left after
   step 2 is applied. On a tie the promo code wins.
Discounts never take the goods below zero.
"""
from decimal import Decimal

from .constants import (
    BULK_MIN_QTY,
    BULK_RATE,
    LOYALTY_CAP,
    LOYALTY_RATE_PER_YEAR,
    PROMO_CODES,
    WHOLESALE_RATE,
)
from .models import Order


def bulk_discount(order: Order) -> Decimal:
    """Total bulk discount over all qualifying lines."""
    total = Decimal(0)
    for item in order.items:
        if item.qty >= BULK_MIN_QTY:
            total += item.qty * item.unit_price * BULK_RATE
    return total


def wholesale_discount(order: Order, amount: Decimal) -> Decimal:
    return amount * WHOLESALE_RATE if order.customer_type == "wholesale" else Decimal(0)


def promo_discount(order: Order, amount: Decimal) -> Decimal:
    """Saving from the promo code; unknown codes save nothing. Codes are case-insensitive."""
    if not order.promo_code:
        return Decimal(0)
    rule = PROMO_CODES.get(order.promo_code.upper())
    if rule is None:
        return Decimal(0)
    kind, value = rule
    saving = amount * value if kind == "percent" else value
    return min(saving, amount)


def loyalty_rate(years: int) -> Decimal:
    return min(LOYALTY_RATE_PER_YEAR * years, LOYALTY_CAP)


def loyalty_discount(order: Order, amount: Decimal) -> Decimal:
    return amount * loyalty_rate(order.loyalty_years)


def apply_discounts(order: Order, subtotal: Decimal) -> tuple[Decimal, list[str]]:
    """Return (total discount, names of the rules that applied)."""
    applied: list[str] = []
    bulk = bulk_discount(order)
    if bulk:
        applied.append("bulk")
    remaining = subtotal - bulk
    wholesale = wholesale_discount(order, remaining)
    if wholesale:
        applied.append("wholesale")
    remaining -= wholesale
    promo = promo_discount(order, remaining)
    loyalty = loyalty_discount(order, remaining)
    if promo and promo >= loyalty:
        applied.append("promo")
        best = promo
    elif loyalty:
        applied.append("loyalty")
        best = loyalty
    else:
        best = Decimal(0)
    return bulk + wholesale + best, applied
