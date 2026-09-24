"""Middleware receives (context, next_handler); lower priorities execute first."""

REGISTRY = []


def middleware(priority):
    def register(cls):
        REGISTRY.append((priority, cls))
        return cls

    return register


def run(context, terminal, instances):
    def call(index):
        if index == len(instances):
            return terminal()
        return instances[index].handle(context, lambda: call(index + 1))

    return call(0)


@middleware(10)
class Logging:
    def handle(self, ctx, nxt):
        ctx.state.setdefault("events", []).append("request")
        nxt()
        ctx.state["events"].append("response")
