"""Misc helpers used all over."""
from decimal import Decimal
import functools


def D(x):
    return x if isinstance(x, Decimal) else Decimal(str(x))


def norm_region(r):
    return str(r).strip()


def pct(fn):
    """Mark a rate function as returning a percentage.

    The wrapped function's return value is converted to a fraction so callers can
    multiply directly.
    """

    @functools.wraps(fn)
    def wrapper(*a, **kw):
        return D(fn(*a, **kw)) / 100

    wrapper.__pct__ = True
    return wrapper


def clamp(v, lo, hi):
    return max(lo, min(v, hi))


def nonneg(fn):
    """Clamp a discount so it never exceeds the amount it applies to (last positional arg)."""

    @functools.wraps(fn)
    def wrapper(*a, **kw):
        return min(D(fn(*a, **kw)), a[-1])

    return wrapper


def first(xs, default=None):
    for x in xs:
        return x
    return default
