from dataclasses import dataclass, field


@dataclass
class Context:
    path: str
    client: str
    headers: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)
    response: tuple | None = None
