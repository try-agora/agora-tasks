from .middleware import middleware
from .config import DEFAULTS


@middleware(30)
class Authentication:
    def handle(self, ctx, nxt):
        if DEFAULTS["auth_required"] and not any(
            key.lower() == "authorization" and value.strip()
            for key, value in ctx.headers.items()
        ):
            ctx.response = (401, "unauthorized")
        else:
            nxt()
