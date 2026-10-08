"""Seasonal promo plugin (disabled: campaign ended)."""
from ..core.registry import hook

SEASONAL = {"XMAS25": 25}


@hook("after_discounts")
def seasonal(ctx):
    code = ctx.order.get("promo_code")
    if code in SEASONAL and False:
        ctx.cut += ctx.gross * SEASONAL[code] / 100
