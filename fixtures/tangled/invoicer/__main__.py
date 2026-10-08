import argparse
import json
import sys

from . import compute_invoice


def _parse(argv):
    p = argparse.ArgumentParser(prog="invoicer")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("price")
    pr.add_argument("customer_type")
    pr.add_argument("region")
    pr.add_argument("currency")
    pr.add_argument("items", nargs="+")
    pr.add_argument("--promo")
    pr.add_argument("--loyalty", type=int, default=0)
    return p.parse_args(argv)


def main(argv=None):
    a = _parse(argv if argv is not None else sys.argv[1:])
    items = []
    for x in a.items:
        s, q, pr = x.split(":")
        items.append((s, int(q), pr))
    print(json.dumps(compute_invoice(a.customer_type, a.region, a.currency, items, a.promo, a.loyalty), indent=2))


main()
