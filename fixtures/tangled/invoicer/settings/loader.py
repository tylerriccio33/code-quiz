"""Layered configuration: defaults -> settings.json -> environment.

Environment variables named ``INVOICER__<KEY>__<SUBKEY>`` override any setting, e.g.
``INVOICER__TAX__US=8``.
"""
import copy
import json
import os
from pathlib import Path

from .defaults import DEFAULTS
from . import regions

_FILE = Path(__file__).with_name("settings.json")


def _merge(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict) and k != "promos":
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def _from_env(cfg):
    for key, val in os.environ.items():
        if not key.startswith("INVOICER__"):
            continue
        path = key[len("INVOICER__"):].lower().split("__")
        node = cfg
        for p in path[:-1]:
            node = node.setdefault(p, {})
        node[path[-1]] = val
    return cfg


def load():
    cfg = copy.deepcopy(DEFAULTS)
    if _FILE.exists():
        _merge(cfg, json.loads(_FILE.read_text()))
    cfg = _from_env(cfg)
    regions.apply(cfg)
    return cfg
