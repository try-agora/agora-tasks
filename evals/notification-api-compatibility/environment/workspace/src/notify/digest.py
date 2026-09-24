from .core import build_payload


def digest(lines):
    return build_payload("; ".join(lines))
