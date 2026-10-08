"""Tax plugin."""
import os

from ..core.helpers import D
from ..core.registry import step
from ..settings import CONFIG


def rate_for(region):
    env = os.getenv("PRICING_TAX_RATE_" + region)
    if env:
        return D(env)
    return D(CONFIG["tax"][region]) / 100


def apply_tax(ctx):
    region = ctx.order["region"]
    base = ctx.net + ctx.handling if region in CONFIG["ship_tax"] else ctx.net
    return base * rate_for(region)


@step("tax", 40)
def _tax_step(ctx):
    from ..money import to_money

    ctx.levy = to_money(apply_tax(ctx), ctx.order["currency"])
