"""Run fixtures/clean and fixtures/tangled on the same inputs; assert identical output.
Also verifies every gold answer in examples/clean.yaml / examples/tangled.yaml by running the code.

    uv run python fixtures/check_equivalence.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

RUNNER = r"""
import json, sys
from invoicer import compute_invoice
out = []
for c in json.loads(sys.stdin.read()):
    try:
        out.append(compute_invoice(*c["args"], **c.get("kw", {})))
    except ValueError as e:
        out.append({"error": type(e).__name__})
print(json.dumps(out))
"""

CASES = [
    {"args": ["wholesale", "EU", "EUR", [["A", 12, "9.99"], ["B", 1, "40"]]], "kw": {"promo_code": "SAVE10"}},
    {"args": ["retail", "US", "USD", [["W", 3, "19.99"]]], "kw": {"loyalty_years": 3}},
    {"args": ["retail", "US", "USD", [["W", 3, "19.99"]]], "kw": {"loyalty_years": 9, "promo_code": "save10"}},
    {"args": ["vip", "UK", "GBP", [["X", 1, "15.00"]]]},
    {"args": ["retail", "CA", "USD", [["X", 2, "20.00"]]]},
    {"args": ["retail", "CA", "USD", [["X", 1, "100.00"]]]},
    {"args": ["retail", "EU", "JPY", [["J", 3, "1234"], ["K", 10, "55"]]], "kw": {"promo_code": "FLAT20"}},
    {"args": ["wholesale", "US", "USD", [["A", 9, "10.00"]]], "kw": {"loyalty_years": 10}},
    {"args": ["wholesale", "US", "USD", [["A", 10, "10.00"]]], "kw": {"loyalty_years": 10}},
    {"args": ["retail", "UK", "GBP", [["A", 1, "10.00"]]], "kw": {"promo_code": "FLAT20"}},
    {"args": ["retail", "US", "USD", [["A", 1, "99.99"]]]},
    {"args": ["retail", "US", "USD", [["A", 1, "100.00"]]]},
    {"args": ["retail", "EU", "EUR", [["A", 1, "50.00"]]], "kw": {"promo_code": "WELCOME5", "loyalty_years": 2}},
    {"args": ["retail", "US", "USD", [["A", 1, "50.00"]]], "kw": {"promo_code": "SAVE10", "loyalty_years": 10}},
    {"args": ["retail", "US", "USD", [["A", 1, "50.00"]]], "kw": {"promo_code": "XMAS25"}},
    {"args": ["retail", "us", "USD", [["A", 1, "0.125"]]]},
    {"args": ["retail", "US", "USD", [["A", 1, "0.125"]]]},
    {"args": ["retail", "US", "USD", [["A", 1, "0.135"]]]},
    {"args": ["bogus", "US", "USD", [["A", 1, "1"]]]},
    {"args": ["retail", "US", "USD", [["A", 2, "30.00"]]]},
]


def run(which, cases, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith(("PRICING_", "INVOICER_"))}
    e.update(env or {})
    e["PYTHONPATH"] = str(HERE / which)
    r = subprocess.run([sys.executable, "-c", RUNNER], input=json.dumps(cases), env=e,
                       capture_output=True, text=True, cwd=HERE / which, check=True)
    return json.loads(r.stdout)


def both(cases, env=None):
    a, b = run("clean", cases, env), run("tangled", cases, env)
    for c, x, y in zip(cases, a, b):
        assert x == y, f"MISMATCH {c} env={env}\n clean  ={x}\n tangled={y}"
    return a


def one(args, kw=None, env=None):
    return both([{"args": args, "kw": kw or {}}], env)[0]


def main():
    res = both(CASES)
    for c, r in zip(CASES, res):
        print(c["args"][:3], c.get("kw", {}), "->", r)
    for env in ({"PRICING_TAX_RATE_US": "0.10"}, {"PRICING_TAX_RATE_CA": "0.05"},
                {"INVOICER__TAX__US": "8"}):
        both(CASES, env)
    print(f"equivalent on {len(CASES)} cases x 4 environments")

    # ---- gold answers for the quiz
    gold = {}
    gold["total_wholesale_eu"] = one(["wholesale", "EU", "EUR", [["A", 12, "9.99"], ["B", 1, "40"]]], {"promo_code": "SAVE10"})["total"]
    gold["total_retail_us_loyalty"] = one(["retail", "US", "USD", [["W", 3, "19.99"]]], {"loyalty_years": 3})["total"]
    gold["tax_jpy"] = one(["retail", "EU", "JPY", [["J", 3, "1234"], ["K", 10, "55"]]], {"promo_code": "FLAT20"})["tax"]
    # rounding: 0.125 -> 0.12 and 0.135 -> 0.14 is HALF_EVEN
    r1 = one(["vip", "US", "USD", [["A", 1, "0.125"]]])["subtotal"]
    r2 = one(["vip", "US", "USD", [["A", 1, "0.135"]]])["subtotal"]
    gold["rounding"] = "B" if (r1, r2) == ("0.12", "0.14") else f"? {r1} {r2}"
    base = one(["retail", "US", "USD", [["A", 2, "30.00"]]])
    over = one(["retail", "US", "USD", [["A", 2, "30.00"]]], env={"PRICING_TAX_RATE_US": "0.10"})
    gold["env_override_works"] = (base["tax"], over["tax"], over["total"])
    gold["inv_env_ignored"] = one(["retail", "US", "USD", [["A", 2, "30.00"]]], env={"INVOICER__TAX__US": "8"}) == base
    gold["rules_wholesale_eu"] = one(["wholesale", "EU", "EUR", [["A", 12, "9.99"], ["B", 1, "40"]]], {"promo_code": "SAVE10", "loyalty_years": 2})["applied"]
    p = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "SAVE10", "loyalty_years": 3})["applied"]
    l = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "SAVE10", "loyalty_years": 0})["applied"]
    w = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "FLAT20", "loyalty_years": 5})["applied"]
    gold["promo_vs_loyalty"] = (p, l, w)  # larger wins; no stacking
    t = one(["retail", "US", "USD", [["A", 1, "200.00"]]], {"promo_code": "FLAT20", "loyalty_years": 10})["applied"]
    gold["tie_promo_wins"] = t  # FLAT20 = 20 = 10%? no: loyalty cap 5% = 10 -> promo. tie case below
    tie = one(["retail", "US", "USD", [["A", 1, "400.00"]]], {"promo_code": "FLAT20", "loyalty_years": 5})["applied"]
    gold["tie"] = tie  # 5% of 400 = 20 = FLAT20
    ca = one(["retail", "CA", "USD", [["X", 1, "200.00"]]])
    gold["ca_rate_pct"] = float(ca["tax"]) / 200 * 100
    gold["ship_threshold"] = (one(["retail", "US", "USD", [["A", 1, "99.99"]]])["shipping"], one(["retail", "US", "USD", [["A", 1, "100.00"]]])["shipping"])
    gold["bulk_min_qty"] = (one(["retail", "US", "USD", [["A", 9, "1"]]])["applied"], one(["retail", "US", "USD", [["A", 10, "1"]]])["applied"])
    ws = one(["wholesale", "US", "USD", [["A", 1, "200.00"]]])
    gold["wholesale_pct"] = float(ws["discount"]) / 200 * 100
    taxed = {}
    for reg in ["US", "EU", "UK", "CA"]:
        r = one(["retail", reg, "USD", [["A", 1, "10.00"]]])
        rate = float(one(["retail", reg, "USD", [["A", 1, "200.00"]]])["tax"]) / 200
        taxed[reg] = abs(float(r["tax"]) - round(rate * (10 + float(r["shipping"])), 2)) < 0.006
    gold["shipping_taxed"] = sorted(k for k, v in taxed.items() if v)
    gold["promo_case_insensitive"] = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "save10"})["applied"]
    gold["vip_shipping"] = one(["vip", "CA", "USD", [["A", 1, "10.00"]]])["shipping"]
    gold["xmas25"] = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "XMAS25"})["discount"]
    gold["loyalty_cap"] = float(one(["retail", "US", "USD", [["A", 1, "100.00"]]], {"loyalty_years": 20})["discount"])
    gold["loyalty_beats_small_promo"] = one(["retail", "US", "USD", [["A", 1, "1000.00"]]], {"promo_code": "FLAT20", "loyalty_years": 5})["applied"]
    gold["welcome5"] = one(["retail", "US", "USD", [["A", 1, "50.00"]]], {"promo_code": "WELCOME5"})["applied"]
    for k, v in gold.items():
        print(f"{k:28} {v}")
    # the quiz's gold answers (examples/clean.yaml == examples/tangled.yaml)
    expect = {
        "total_wholesale_eu": "146.26", "total_retail_us_loyalty": "69.74", "tax_jpy": "841",
        "rounding": "B", "env_override_works": ("4.20", "6.00", "73.50"), "inv_env_ignored": True,
        "rules_wholesale_eu": ["bulk", "wholesale", "promo"], "tie": ["promo"],
        "loyalty_beats_small_promo": ["loyalty"], "ca_rate_pct": 13.0,
        "ship_threshold": ("7.50", "0.00"), "bulk_min_qty": ([], ["bulk"]), "wholesale_pct": 12.0,
        "shipping_taxed": ["CA", "EU", "UK"], "promo_case_insensitive": ["promo"],
        "vip_shipping": "0.00", "welcome5": [], "loyalty_cap": 5.0,
    }
    for k, v in expect.items():
        assert gold[k] == v, (k, gold[k], v)
    print("all quiz answers verified")


if __name__ == "__main__":
    main()
