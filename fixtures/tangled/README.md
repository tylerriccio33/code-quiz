# invoicer 2.x

Pluggable invoice pricing.

    python -m invoicer price wholesale EU EUR A:12:9.99 B:1:40 --promo SAVE10

## Rules
- Bulk: 5% off lines of 12+ units.
- Wholesale: 15% trade discount.
- Promo codes (SAVE10, FLAT20, WELCOME5) and loyalty (1%/year, max 5%) stack.
- Free shipping over 150.

## Money
Amounts are rounded HALF_UP to the currency precision.

## Configuration
Defaults live in `invoicer/settings/defaults.py` (the single source of truth). Override any
value with `INVOICER__<KEY>__<SUBKEY>`, e.g. `INVOICER__TAX__US=8` sets the US tax rate.
Canada is taxed at 5% GST.
