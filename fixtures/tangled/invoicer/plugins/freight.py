"""Shipping plugin. Free shipping over 150 in the order currency."""
from ..core.helpers import D
from ..core.registry import step
from ..settings import CONFIG


class _FreeForVip:
    def waived(self, ctx):
        return ctx.order["customer_type"] == "vip" or super().waived(ctx)


class _Threshold:
    LIMIT = D(100)

    def waived(self, ctx):
        return ctx.net >= self.LIMIT


class Freight(_FreeForVip, _Threshold):
    def fee(self, ctx):
        if self.waived(ctx):
            return D(0)
        return D(CONFIG["shipping"][ctx.order["region"]])


@step("handling", 30)
def handling(ctx):
    from ..money import to_money

    ctx.handling = to_money(Freight().fee(ctx), ctx.order["currency"])
