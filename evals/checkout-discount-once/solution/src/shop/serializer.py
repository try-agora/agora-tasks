def serialize(order):
    return {"account": order["account"], "total": format(order["total"], ".2f")}
