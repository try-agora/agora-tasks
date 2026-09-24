from .dedup import dedup_by
from .normalize import canonical


def dedup_accounts(records):
    return dedup_by(records, lambda row: canonical(row["account"]))
