from decimal import Decimal

from .base import ConfiguredMixin, Rule
from ..core.helpers import D, pct


class BulkLineRule(ConfiguredMixin, Rule):
    """5% off every line with a dozen or more units."""

    key = "bulk"
    priority = 10

    @pct
    def rate(self):
        return self.cfg["bulk"]["pct"]

    def amount(self, ctx, base):
        total = Decimal(0)
        for sku, qty, price in ctx.order["items"]:
            if qty >= self.cfg["bulk"]["min_qty"]:
                total += qty * D(price) * self.rate()
        return total
