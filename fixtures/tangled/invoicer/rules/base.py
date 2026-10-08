"""Base classes for rules.

Rules are applied in ascending ``priority``. Every rule's discount is computed on the
amount left after the previous rules, and all applicable rules stack.
"""
from decimal import Decimal

from ..core.registry import RuleMeta


class Rule(metaclass=RuleMeta):
    abstract = True
    key = None
    priority = 100
    group = None  # rules sharing a group are mutually exclusive

    def applies(self, ctx):
        return True

    def amount(self, ctx, base):
        return Decimal(0)


class ConfiguredMixin:
    @property
    def cfg(self):
        from ..settings import CONFIG

        return CONFIG


class CustomerTypeMixin:
    customer_types = ()

    def applies(self, ctx):
        return ctx.order["customer_type"] in self.customer_types
