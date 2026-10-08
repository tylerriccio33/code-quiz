# invoicer

Prices an order: subtotal, discounts, shipping, tax, total.

    python -m invoicer price wholesale EU EUR A:12:9.99 B:1:40 --promo SAVE10

All constants live in `invoicer/constants.py`. The pipeline is in `invoicer/engine.py`.
Rules (see `discounts.py`): bulk line discount, wholesale discount, then the better of promo
code or loyalty (promo wins ties). Rounding is ROUND_HALF_EVEN per component.
Tax override: `PRICING_TAX_RATE_<REGION>`.
