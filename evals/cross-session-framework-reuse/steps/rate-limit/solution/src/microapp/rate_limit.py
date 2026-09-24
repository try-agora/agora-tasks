from .middleware import middleware
from .config import DEFAULTS


@middleware(30)
class RateLimit:
    def __init__(self):
        self.counts = {}

    def handle(self, ctx, nxt):
        self.counts[ctx.client] = self.counts.get(ctx.client, 0) + 1
        if self.counts[ctx.client] > DEFAULTS["rate_limit"]:
            ctx.response = (429, "too many requests")
        else:
            nxt()
