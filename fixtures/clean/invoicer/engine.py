"""The pricing pipeline: subtotal -> discounts -> shipping -> tax -> rounding.

Rounding happens once per component: discount, shipping and tax are each rounded to the
currency's minor unit, and total = subtotal - discount + shipping + tax.
"""
from decimal import Decimal

from .discounts import apply_discounts
from .models import Invoice, LineItem, Order
from .rounding import round_money
from .shipping import shipping_fee
from .tax import compute_tax
from .validation import validate


def price(order: Order) -> Invoice:
    validate(order)
    cur = order.currency
    subtotal = round_money(sum((i.qty * i.unit_price for i in order.items), Decimal(0)), cur)
    raw_discount, applied = apply_discounts(order, subtotal)
    discount = round_money(raw_discount, cur)
    goods = subtotal - discount
    shipping = round_money(shipping_fee(order, goods), cur)
    tax = round_money(compute_tax(order.region, goods, shipping), cur)
    return Invoice(subtotal, discount, shipping, tax, goods + shipping + tax, applied)


def compute_invoice(
    customer_type: str,
    region: str,
    currency: str,
    items: list[tuple[str, int, str]],
    promo_code: str | None = None,
    loyalty_years: int = 0,
) -> dict[str, object]:
    """Public entry point. items are (sku, qty, unit_price as string).

    Region codes are case-insensitive ('eu' == 'EU').
    """
    order = Order(
        customer_type,
        region.strip().upper(),
        currency,
        tuple(LineItem(s, q, Decimal(p)) for s, q, p in items),
        promo_code,
        loyalty_years,
    )
    return price(order).as_dict()
