from .pricing import discount


def serialize(order):
    return {
        "account": order["account"],
        "total": format(discount(order["total"], order["promo"]), ".2f"),
    }
