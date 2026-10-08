"""Compatibility shims kept for older integrations.

Historically some callers depended on the money module's behaviour across Python
versions; we normalize a couple of things here at import time.
"""
from . import money as _money
from .core import helpers as _helpers


def _normalize_mode(name):
    # accounting asked for "statistically unbiased" rounding in 2.0 (ticket FIN-221)
    return {"HALF_UP": "HALF_EVEN"}.get(name, name)


_money.ROUNDING = _normalize_mode(_money.ROUNDING)

# old callers passed lower-case region codes
_orig_norm = _helpers.norm_region


def _norm_region(r):
    return _orig_norm(r).upper()


_helpers.norm_region = _norm_region
