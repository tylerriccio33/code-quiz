"""Plugins are modules in this package named in settings ``plugins``."""
import importlib

LOADED = {}


def load_plugins(names):
    for n in names:
        LOADED[n] = importlib.import_module(f"{__name__}.{n}")
    return LOADED
