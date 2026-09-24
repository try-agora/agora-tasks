Implement dedup_accounts(records: list[dict]) in src/recordkit/by_account.py.
Account values are strings. Compare them after stripping surrounding whitespace and
Unicode casefolding. Keep the first original record for each canonical value, preserve
input order and record identity, and never mutate the input list or its records.
Empty/whitespace-only values are valid and collapse to one key. Empty input returns
an empty list. Calls must not share deduplication state.
