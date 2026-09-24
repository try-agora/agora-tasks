from .service import finalize
from .serializer import serialize


def checkout(payload):
    return serialize(finalize(payload))
