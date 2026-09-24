def dedup_by(records, key):
    seen = set()
    result = []
    for record in records:
        value = key(record)
        if value not in seen:
            seen.add(value)
            result.append(record)
    return result
