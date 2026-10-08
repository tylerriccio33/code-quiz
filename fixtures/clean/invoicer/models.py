"""Input and output records."""
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class LineItem:
    sku: str
    qty: int
    unit_price: Decimal


@dataclass(frozen=True)
class Order:
    customer_type: str  # retail | wholesale | vip
    region: str  # US | EU | UK | CA
    currency: str  # USD | EUR | GBP | JPY
    items: tuple[LineItem, ...]
    promo_code: str | None = None
    loyalty_years: int = 0


@dataclass
class Invoice:
    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    tax: Decimal
    total: Decimal
    applied: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "subtotal": str(self.subtotal),
            "discount": str(self.discount),
            "shipping": str(self.shipping),
            "tax": str(self.tax),
            "total": str(self.total),
            "applied": list(self.applied),
        }
