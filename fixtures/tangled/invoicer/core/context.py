"""Pricing context shared by steps and rules."""
from decimal import Decimal


class Bag(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


class PricingContext(Bag):
    """Holds the order and the running numbers.

    ``net`` is the amount after discounts (pre-tax), ``gross`` the amount before discounts.
    """

    @classmethod
    def new(cls, order):
        c = cls(order=order, applied=[], gross=Decimal(0), net=Decimal(0))
        c.cut = Decimal(0)
        c.handling = Decimal(0)
        c.levy = Decimal(0)
        return c
