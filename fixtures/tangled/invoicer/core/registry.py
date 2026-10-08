"""String-keyed registries filled at import time."""

RULES = {}
STEPS = {}
HOOKS = {"after_discounts": [], "before_tax": []}


class RuleMeta(type):
    """Every concrete rule class registers itself under its ``key``."""

    def __new__(mcls, name, bases, ns):
        cls = super().__new__(mcls, name, bases, ns)
        key = ns.get("key")
        if key and not ns.get("abstract", False):
            RULES[key] = cls()
        return cls


def step(name, order):
    def deco(fn):
        STEPS[name] = (order, fn)
        return fn

    return deco


def hook(event):
    def deco(fn):
        HOOKS[event].append(fn)
        return fn

    return deco
