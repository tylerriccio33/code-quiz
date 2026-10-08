"""Tax rates and tax computation."""
import os
from decimal import Decimal

from .constants import SHIPPING_TAXED_REGIONS, TAX_ENV_PREFIX, TAX_RATES


def tax_rate(region: str) -> Decimal:
    """Rate for the region; env var PRICING_TAX_RATE_<REGION> (e.g. 0.19) overrides it."""
    override = os.environ.get(TAX_ENV_PREFIX + region)
    if override:
        return Decimal(override)
    return TAX_RATES[region]


def taxable_amount(region: str, goods: Decimal, shipping: Decimal) -> Decimal:
    """Goods are always taxed; shipping only in SHIPPING_TAXED_REGIONS."""
    return goods + shipping if region in SHIPPING_TAXED_REGIONS else goods


def compute_tax(region: str, goods: Decimal, shipping: Decimal) -> Decimal:
    return taxable_amount(region, goods, shipping) * tax_rate(region)
