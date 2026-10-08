"""Input validation."""
from .constants import CURRENCY_DECIMALS, CUSTOMER_TYPES, TAX_RATES
from .models import Order


class InvalidOrder(ValueError):
    pass


def validate(order: Order) -> None:
    if order.customer_type not in CUSTOMER_TYPES:
        raise InvalidOrder(f"unknown customer type {order.customer_type!r}")
    if order.region not in TAX_RATES:
        raise InvalidOrder(f"unknown region {order.region!r}")
    if order.currency not in CURRENCY_DECIMALS:
        raise InvalidOrder(f"unknown currency {order.currency!r}")
    if not order.items:
        raise InvalidOrder("order has no items")
    for item in order.items:
        if item.qty <= 0 or item.unit_price < 0:
            raise InvalidOrder(f"bad line {item.sku!r}")
    if order.loyalty_years < 0:
        raise InvalidOrder("negative loyalty_years")
