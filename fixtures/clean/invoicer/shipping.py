"""Shipping fees."""
from decimal import Decimal

from .constants import FREE_SHIPPING_THRESHOLD, SHIPPING_FEES, VIP_FREE_SHIPPING
from .models import Order


def shipping_fee(order: Order, discounted_goods: Decimal) -> Decimal:
    """Flat regional fee; free for VIPs or when discounted goods >= FREE_SHIPPING_THRESHOLD."""
    if VIP_FREE_SHIPPING and order.customer_type == "vip":
        return Decimal(0)
    if discounted_goods >= FREE_SHIPPING_THRESHOLD:
        return Decimal(0)
    return SHIPPING_FEES[order.region]
