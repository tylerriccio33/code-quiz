"""CLI: python -m invoicer price CUSTOMER REGION CURRENCY SKU:QTY:PRICE... [--promo C] [--loyalty N]"""
import argparse
import json

from .engine import compute_invoice


def main() -> None:
    p = argparse.ArgumentParser(prog="invoicer")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("price")
    pr.add_argument("customer_type")
    pr.add_argument("region")
    pr.add_argument("currency")
    pr.add_argument("items", nargs="+", help="SKU:QTY:PRICE")
    pr.add_argument("--promo")
    pr.add_argument("--loyalty", type=int, default=0)
    a = p.parse_args()
    items = [(s, int(q), pr_) for s, q, pr_ in (x.split(":") for x in a.items)]
    print(json.dumps(compute_invoice(a.customer_type, a.region, a.currency, items, a.promo, a.loyalty), indent=2))


if __name__ == "__main__":
    main()
