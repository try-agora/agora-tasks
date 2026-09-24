Repair Buffer.acknowledge(ids) in src/buffer.py.
Delete only the acknowledged positive integer IDs, preserving other payloads and their order.
Duplicate and unknown IDs are harmless; empty input changes nothing. Accept any finite
iterable, including generators. Reject booleans, non-integers, zero, and negative IDs
with ValueError before deleting anything. If iteration or a database operation fails,
propagate the exception and leave every row unchanged. Successful deletions must survive
closing and reopening the database. Do not renumber surviving IDs or change the existing API.
Reclaiming SQLite pages for reuse is sufficient; file compaction is outside the contract.
