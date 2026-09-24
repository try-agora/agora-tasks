from .core import build_payload


def alert(text):
    return build_payload(text)
