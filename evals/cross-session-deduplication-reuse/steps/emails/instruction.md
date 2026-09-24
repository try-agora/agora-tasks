The source workspace has been restored to its original baseline.
Implement dedup_emails(records: list[dict]) in src/recordkit/by_email.py.
For this export system, the whole email field is a case-insensitive identifier;
this is an explicit product policy, not a general claim about email standards.
Compare strings after stripping surrounding whitespace and Unicode casefolding.
Keep the first original record for each canonical value and preserve input order
and object identity. Never mutate input or share state across calls. Empty values
are valid; an empty input produces an empty list.
