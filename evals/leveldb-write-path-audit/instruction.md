# Trace a write from the public API to durability and reader visibility

Before changing batching policy, audit the frozen LevelDB 1.23 source under
`/app/src/leveldb`. Follow a normal nonempty `Put` through the public convenience
API, queued writers, log records, batch callbacks, the memtable's index, and the
sequence number that ordinary reads observe. This is a source audit, not a repair.

Use `DBImpl::Put` and `MemTable::Add` as the write-path navigation endpoints,
then connect publication to the sequence bound chosen by `DBImpl::Get`. The
intermediate durability, dispatch, and ordering evidence is specified below.

Write `/app/src/write-path.json` with exactly `locations` and `decisions` objects.
Each location is `{"file": "leveldb/path/file.cc", "symbol": "Class::Method",
"line": 42}`. Paths are relative to `/app/src`; retain nested class names but
omit namespaces and template arguments (for example, `Outer::Inner::Method`).
Give the first line of the decisive expression, not its enclosing declaration.

Include these location keys:

| Key | Decisive expression |
| --- | --- |
| `public_put` | Concrete DB implementation delegates its single-key Put to the base convenience method. |
| `batch_write` | Base Put delegates the assembled batch to the virtual Write method. |
| `batch_key` | Put encodes the user key into the batch as a length-prefixed slice. |
| `group_sync_fence` | Test that prevents a synchronous follower from joining an asynchronous leader. |
| `wal_append` | Queued write appends the assembled batch contents to the log. |
| `wal_sync` | Queued write requests a durable sync of the log file. |
| `memtable_dispatch` | Queued write dispatches the completed batch into the memtable. |
| `batch_iteration` | Internal batch helper starts iteration with the memtable inserter. |
| `put_callback` | Batch iteration invokes its handler for a decoded Put record. |
| `entry_insert` | Concrete memtable inserter adds a value record with its sequence number. |
| `memtable_index` | Memtable adds the encoded entry into its underlying sorted index. |
| `node_publication` | Index node link setter publishes a successor using release ordering. |
| `posix_sync` | POSIX writable-file Sync delegates to its file-descriptor sync helper. |
| `sequence_publication` | Queued write publishes the group's final sequence number. |
| `read_sequence` | Ordinary Get chooses its sequence bound when no snapshot was supplied. |

Derive these `decisions` from the same implementation:

- `successful_sync_order`: order of `wal`, `sync`, `memtable`, `sequence` for a
  successful synchronous group leader.
- `writer_mutex_held_during_wal`: boolean, during log append in that path.
- `sync_follower_can_join_async_leader`: boolean, ignoring size limits.
- `async_follower_can_join_sync_leader`: boolean, ignoring size limits.
- `sequence_advances_per_record`: boolean; distinct sequence for each Put/Delete
  in a batch rather than one shared number for all records.
- `delete_representation`: `tombstone` or `physical_removal` in the memtable.
- `posix_flush_is_durable_sync`: boolean; does Flush itself perform a durable
  file-descriptor sync, rather than only draining the process's buffer?
- `posix_linux_sync_call`: syscall name for `HAVE_FDATASYNC=1` and
  `HAVE_FULLFSYNC=0`, excluding namespace punctuation.
- `sync_error_blocks_future_writes`: boolean, after the leader's log Sync fails.
- `read_without_snapshot_uses`: `last_published_sequence`, `unbounded`, or
  `largest_current_memtable_sequence`.
- `default_group_limit_bytes`: integer maximum used before the small-first-batch
  adjustment.
- `small_group_extra_bytes`: integer added to the first batch's byte size in that
  small-batch adjustment.

Assume there is room in the current memtable and no compaction or recovery is
needed. Use the POSIX file implementation, not Windows or the in-memory test Env.
Except the explicitly requested Sync-error decision, assume operations succeed.
Do not modify `src/leveldb`. Scratch scripts elsewhere in `/app` are allowed.
No compilation, dependency installation, or network access is necessary.
