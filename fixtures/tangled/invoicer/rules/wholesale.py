from .base import ConfiguredMixin, CustomerTypeMixin, Rule
from ..core.helpers import pct


class WholesaleRule(CustomerTypeMixin, ConfiguredMixin, Rule):
    """Trade discount (15%) for wholesale accounts."""

    key = "wholesale"
    priority = 20
    customer_types = ("wholesale",)

    @pct
    def rate(self):
        return self.cfg["wholesale_pct"]

    def amount(self, ctx, base):
        return base * self.rate()
