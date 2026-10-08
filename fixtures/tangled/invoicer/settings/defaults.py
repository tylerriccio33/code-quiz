"""Built-in defaults. Rates are percentages (the rules convert them).

These are the single source of truth for pricing parameters.
"""

DEFAULTS = {
    "currencies": {
        "USD": {"exp": 2},
        "EUR": {"exp": 2},
        "GBP": {"exp": 2},
        "JPY": {"exp": 0},
    },
    "tax": {"US": 7, "EU": 20, "UK": 20, "CA": 5},
    "ship_tax": ["EU", "UK"],
    "shipping": {"US": "7.50", "EU": "9.00", "UK": "9.00", "CA": "12.00"},
    "bulk": {"min_qty": 12, "pct": 5},
    "wholesale_pct": 15,
    "loyalty": {"per_year": 1, "max": 5},
    "promos": {"SAVE10": ["pct", 10], "FLAT20": ["abs", 20], "WELCOME5": ["pct", 5]},
    "plugins": ["vat", "freight", "promos"],
    "customer_types": ["retail", "wholesale", "vip"],
}
