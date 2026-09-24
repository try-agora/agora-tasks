import re
from urllib.parse import urlsplit


def parse_remote(value):
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        raise ValueError("invalid remote")
    if "://" not in value:
        match = re.fullmatch(
            r"(?:(?P<user>[^@/:]+)@)?(?P<host>[^/:]+):(?P<path>.+)", value
        )
        if not match:
            raise ValueError("expected an absolute URL or SCP-style SSH remote")
        value = (
            "ssh://"
            + (match["user"] + "@" if match["user"] else "")
            + match["host"]
            + "/"
            + match["path"]
        )
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid port or host") from exc
    if (
        parsed.scheme not in ("ssh", "https")
        or not parsed.hostname
        or parsed.password is not None
    ):
        raise ValueError("unsupported remote")
    if parsed.query or parsed.fragment:
        raise ValueError("unexpected query or fragment")
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError("invalid repository path")
    return {
        "transport": parsed.scheme,
        "host": parsed.hostname.lower(),
        "port": port if port is not None else (22 if parsed.scheme == "ssh" else 443),
        "user": parsed.username,
        "path": path,
    }
