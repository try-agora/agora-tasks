from decimal import Decimal
from .pricing import discount, taxed


def finalize(payload):
    subtotal = discount(Decimal(str(payload["subtotal"])), payload.get("promo"))
    return {
        "account": payload["account"],
        "promo": payload.get("promo"),
        "total": taxed(subtotal, payload.get("region", "US")),
    }
