"""The step pipeline. Steps are registered by name with an order key and run by name."""
from decimal import Decimal

from .context import PricingContext
from .helpers import D
from .registry import HOOKS, RULES, STEPS, step


@step("subtotal", 10)
def subtotal(ctx):
    from ..money import to_money

    ctx.gross = to_money(
        sum((q * D(p) for _, q, p in ctx.order["items"]), Decimal(0)), ctx.order["currency"]
    )


@step("discounts", 20)
def discounts(ctx):
    from ..money import to_money

    base = ctx.gross
    groups = {}
    for rule in sorted(RULES.values(), key=lambda r: r.priority):
        if not rule.applies(ctx):
            continue
        if rule.group:
            groups.setdefault(rule.group, []).append(rule)
            continue
        amt = D(rule.amount(ctx, base))
        if amt:
            ctx.applied.append(rule.key)
            ctx.cut += amt
            base -= amt
    for members in groups.values():
        scored = [(r.amount(ctx, base), -r.priority, r) for r in members]
        scored = [s for s in scored if s[0]]
        if scored:
            amt, _, best = max(scored, key=lambda s: (s[0], s[1]))
            ctx.applied.append(best.key)
            ctx.cut += amt
    for fn in HOOKS["after_discounts"]:
        fn(ctx)
    ctx.cut = to_money(ctx.cut, ctx.order["currency"])
    ctx.net = ctx.gross - ctx.cut


@step("finish", 90)
def finish(ctx):
    ctx.total = ctx.net + ctx.handling + ctx.levy


def run(order):
    ctx = PricingContext.new(order)
    for name, (_, fn) in sorted(STEPS.items(), key=lambda kv: kv[1][0]):
        fn(ctx)
    return ctx
