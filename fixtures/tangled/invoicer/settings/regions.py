"""Region metadata helpers."""

REGION_NAMES = {"US": "United States", "EU": "European Union", "UK": "United Kingdom", "CA": "Canada"}

# HST harmonisation (ON) -- finance, 2021
_PATCH = {"CA": 13}


def apply(cfg):
    """Fill in derived region data."""
    cfg.setdefault("region_names", dict(REGION_NAMES))
    for r, v in _PATCH.items():
        cfg["tax"][r] = v
    return cfg


def is_eu(region):
    return region in ("EU",)
