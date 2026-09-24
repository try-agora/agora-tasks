from decimal import Decimal, ROUND_HALF_UP

PROMOS = {"SAVE10": Decimal("0.10"), "SAVE20": Decimal("0.20")}
TAX = {"US": Decimal("0.07"), "EU": Decimal("0.20")}


def money(amount):
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def discount(amount, code):
    return money(amount * (1 - PROMOS.get(code, Decimal(0))))


def taxed(amount, region):
    return money(amount * (1 + TAX.get(region, Decimal(0))))
