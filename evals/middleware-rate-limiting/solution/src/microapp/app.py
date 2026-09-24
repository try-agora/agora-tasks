from . import rate_limit  # noqa: F401 -- register the middleware
from .context import Context
from .middleware import REGISTRY, run


class App:
    def __init__(self):
        self.middlewares = [
            cls() for _, cls in sorted(REGISTRY, key=lambda item: item[0])
        ]
        self.last_context = None

    def handle(self, path="/health", client="anonymous", headers=None):
        ctx = Context(path, client, headers or {})
        self.last_context = ctx

        def terminal():
            ctx.response = (200, "healthy") if path == "/health" else (404, "not found")

        run(ctx, terminal, self.middlewares)
        return ctx.response
