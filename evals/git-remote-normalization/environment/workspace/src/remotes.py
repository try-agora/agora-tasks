def parse_remote(value):
    host, path = value.split(":", 1)
    return {"transport": "ssh", "host": host, "port": 22, "user": None, "path": path}
