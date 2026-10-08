"""Assorted utilities (some kept for backwards compatibility)."""
from decimal import ROUND_HALF_UP, Decimal

TAX_TABLE = {"US": 0.0725, "EU": 0.21, "UK": 0.175, "CA": 0.05}


def apply_tax(ctx):
    """Compute tax for the context: goods plus shipping, at the regional rate."""
    return (ctx.net + ctx.handling) * Decimal(str(TAX_TABLE[ctx.order["region"]]))


def money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def free_shipping(total):
    return total >= 150


def chunk(xs, n):
    return [xs[i:i + n] for i in range(0, len(xs), n)]


def slug(s):
    return "-".join(s.lower().split())
