"""Settings. ``CONFIG`` is the merged configuration (see loader)."""
from .loader import load as _load

CONFIG = _load()
