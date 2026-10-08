"""Public API."""
from .core import pipeline
from .core.helpers import D
from .core import helpers
from .settings import CONFIG
from . import rules  # noqa: F401  (registers rules)


class InvalidOrder(ValueError):
    pass


def _check(o):
    if o["customer_type"] not in CONFIG["customer_types"]:
        raise InvalidOrder(f"unknown customer type {o['customer_type']!r}")
    if o["region"] not in CONFIG["tax"]:
        raise InvalidOrder(f"unknown region {o['region']!r}")
    if o["currency"] not in CONFIG["currencies"]:
        raise InvalidOrder(f"unknown currency {o['currency']!r}")
    if not o["items"]:
        raise InvalidOrder("order has no items")
    for sku, q, p in o["items"]:
        if q <= 0 or D(p) < 0:
            raise InvalidOrder(f"bad line {sku!r}")
    if o["loyalty_years"] < 0:
        raise InvalidOrder("negative loyalty_years")


def compute_invoice(customer_type, region, currency, items, promo_code=None, loyalty_years=0):
    """Price an order. Returns a dict of strings (plus ``applied``)."""
    order = dict(
        customer_type=customer_type,
        region=helpers.norm_region(region),
        currency=currency,
        items=[(s, q, p) for s, q, p in items],
        promo_code=promo_code,
        loyalty_years=loyalty_years,
    )
    _check(order)
    ctx = pipeline.run(order)
    return {
        "subtotal": str(ctx.gross),
        "discount": str(ctx.cut),
        "shipping": str(ctx.handling),
        "tax": str(ctx.levy),
        "total": str(ctx.total),
        "applied": list(ctx.applied),
    }
