from decimal import Decimal

from .base import ConfiguredMixin, Rule
from ..core.helpers import D, nonneg


class PromoRule(ConfiguredMixin, Rule):
    """Promo codes. Codes are matched exactly (case-sensitive)."""

    key = "promo"
    priority = 30
    group = "incentive"

    def _lookup(self, code):
        return self.cfg["promos"].get((code or "").upper())

    def applies(self, ctx):
        return self._lookup(ctx.order.get("promo_code")) is not None

    @nonneg
    def amount(self, ctx, base):
        kind, val = self._lookup(ctx.order["promo_code"])
        handler = getattr(self, "_" + kind)
        return handler(base, D(val))

    def _pct(self, base, val):
        return base * val / 100

    def _abs(self, base, val):
        return val

    def _bogo(self, base, val):  # retired 2022
        return Decimal(0)
