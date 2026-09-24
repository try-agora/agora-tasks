import unicodedata
from urllib.parse import quote


def attachment_header(filename):
    if (
        not isinstance(filename, str)
        or not filename
        or any(ord(c) < 32 or ord(c) == 127 for c in filename)
    ):
        raise ValueError("invalid filename")
    fallback = (
        unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode()
        or "download"
    )
    escaped = fallback.replace("\\", "\\\\").replace('"', '\\"')
    result = 'attachment; filename="' + escaped + '"'
    if not filename.isascii():
        result += "; filename*=UTF-8''" + quote(filename, safe="")
    return result
