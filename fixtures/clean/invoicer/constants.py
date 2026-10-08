"""Every business constant used by the invoicer, in one place."""
from decimal import ROUND_HALF_EVEN, Decimal

# Rounding: banker's rounding (half to even) to the currency's minor unit.
ROUNDING_MODE = ROUND_HALF_EVEN

# Number of decimal places per currency.
CURRENCY_DECIMALS = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0}

# Sales tax / VAT rate per region. Override with PRICING_TAX_RATE_<REGION>.
TAX_RATES = {
    "US": Decimal("0.07"),
    "EU": Decimal("0.20"),
    "UK": Decimal("0.20"),
    "CA": Decimal("0.13"),
}
TAX_ENV_PREFIX = "PRICING_TAX_RATE_"

# Regions where shipping is taxed along with the goods.
SHIPPING_TAXED_REGIONS = {"EU", "UK", "CA"}

# Shipping: flat fee per region, waived when the discounted goods reach the threshold.
SHIPPING_FEES = {
    "US": Decimal("7.50"),
    "EU": Decimal("9.00"),
    "UK": Decimal("9.00"),
    "CA": Decimal("12.00"),
}
FREE_SHIPPING_THRESHOLD = Decimal("100")

# Line discount: a line with at least BULK_MIN_QTY units gets BULK_RATE off.
BULK_MIN_QTY = 10
BULK_RATE = Decimal("0.05")

# Order discount for wholesale customers.
WHOLESALE_RATE = Decimal("0.12")

# Promo codes: ("percent", rate) or ("fixed", amount in the order's currency).
PROMO_CODES = {
    "SAVE10": ("percent", Decimal("0.10")),
    "FLAT20": ("fixed", Decimal("20")),
}

# Loyalty: LOYALTY_RATE_PER_YEAR per year, capped at LOYALTY_CAP.
LOYALTY_RATE_PER_YEAR = Decimal("0.01")
LOYALTY_CAP = Decimal("0.05")

CUSTOMER_TYPES = {"retail", "wholesale", "vip"}

# VIP customers never pay shipping.
VIP_FREE_SHIPPING = True
