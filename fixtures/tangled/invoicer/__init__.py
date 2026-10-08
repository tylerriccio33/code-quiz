"""invoicer -- flexible, pluggable invoicing.

Importing the package wires everything up: compatibility shims, settings, the rule
registry and the plugins named in settings. Use ``invoicer.compute_invoice``.
"""
from . import _compat  # noqa: F401  (must come first: patches money handling)
from .settings import CONFIG
from .plugins import load_plugins

load_plugins(CONFIG.get("plugins", []))

from .api import compute_invoice  # noqa: E402

__version__ = "2.3.1"
__all__ = ["compute_invoice", "CONFIG"]
