def build_payload(
    message: str, *, sender: str | None = None, category: str | None = None
) -> dict:
    result = {"msg": message}
    if sender is not None:
        result["sender"] = sender
    if category is not None:
        result["category"] = category
    return result
