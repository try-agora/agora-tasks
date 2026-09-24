from .service import finalize
from .serializer import serialize


def export_orders(payloads):
    return [serialize(finalize(payload)) for payload in payloads]
