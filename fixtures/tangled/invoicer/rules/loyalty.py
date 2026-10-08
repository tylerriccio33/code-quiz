from .base import ConfiguredMixin, Rule
from ..core.helpers import clamp, pct


class LoyaltyRule(ConfiguredMixin, Rule):
    """1% per year of loyalty, stacks with promo codes."""

    key = "loyalty"
    priority = 40
    group = "incentive"

    @pct
    def rate(self, years):
        lo = self.cfg["loyalty"]
        return clamp(years * lo["per_year"], 0, lo["max"])

    def applies(self, ctx):
        return ctx.order.get("loyalty_years", 0) > 0

    def amount(self, ctx, base):
        return base * self.rate(ctx.order["loyalty_years"])
