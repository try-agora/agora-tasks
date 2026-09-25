# Audit LevelDB point reads before changing cache policy

A team wants reads with `fill_cache=false` to avoid cache pollution. Before
changing anything, trace what that flag actually controls in the frozen LevelDB
1.23 source under `/app/src/leveldb`. Follow `DBImpl::Get` through file selection,
`TableCache::Get`, and `Table::InternalGet` to block retrieval and the result
callback. Account for filters, tombstones, and both distinct cache layers.

Write `/app/src/read-cache.json` with exactly `locations` and `decisions` objects.
Each location is `{"file": "leveldb/path/file.cc", "symbol": "Class::Method"}`.
Paths are relative to `/app/src`. Identify the member containing each
responsibility below, without line numbers. Omit namespaces and template
arguments. Free functions use just their name. For a class defined inside a
function, include that enclosing function: `Owner::Method::Local::Callback`.

Include these location keys:

| Key | Responsibility (identify the containing member) |
| --- | --- |
| `memtable_probe` | Point read first probes the mutable memtable. |
| `disk_dispatch` | Point read dispatches to the retained on-disk Version after memtable misses. |
| `level_zero_sort` | Overlap enumeration sorts eligible level-zero files before invoking callbacks. |
| `level_callback` | Version's point read starts overlap enumeration with its local State callback. |
| `table_cache_dispatch` | That local callback dispatches a file lookup, supplying the value-saving callback. |
| `table_lookup` | Table cache probes its cache of open tables by encoded file number. |
| `table_dispatch` | Table cache invokes the table's point-lookup implementation. |
| `filter_gate` | Table point lookup tests whether a decoded block handle can be rejected by its filter. |
| `block_cache_lookup` | Data-block reader probes the block cache using its composite key. |
| `block_cache_insert` | Data-block reader inserts a newly read block into the block cache. |
| `result_callback` | Table point lookup invokes the caller-supplied handler for a valid sought entry. |
| `value_classification` | The saving callback classifies a matching user key as a value or deletion. |
| `filter_user_key` | Internal filter wrapper delegates to the user filter after removing the internal suffix. |
| `filter_region_dispatch` | Filter-block reader delegates an in-range filter region to its policy. |
| `physical_read` | Block-format reader requests block contents plus their trailer from the file. |
| `cached_cleanup` | Data-block reader registers the cleanup that releases a cache handle. |

Derive these `decisions` from the same source:

- `search_order`: array using `table_files`, `immutable_memtable`, and
  `mutable_memtable`, in actual lookup order.
- `read_mutex_held_during_table_get`: boolean, for the DB implementation's mutex.
- `memtable_tombstone_ends_search`: boolean; does a matching visible tombstone in
  the mutable memtable stop the search rather than reveal an older table value?
- `table_tombstone_ends_search`: boolean; does a matching visible tombstone in an
  eligible table stop the search rather than continue into older candidate files?
- `level_zero_order`: `ascending_file_number` or `descending_file_number`.
- `higher_level_candidates`: integer maximum candidate files searched in each
  single level greater than zero for an ordinary point lookup.
- `fill_cache_false_uses_existing_block`: boolean; may an already cached data
  block still satisfy a read whose `fill_cache` is false?
- `fill_cache_false_can_populate_table_cache`: boolean; may a successful first
  open populate the separate table cache despite that read option?
- `fill_cache_false_inserts_data_block`: boolean; may that read insert its newly
  fetched data block into the block cache?
- `cache_hit_rechecks_checksum`: boolean; on a data-block cache hit, does setting
  `verify_checksums=true` perform another checksum calculation on the block?
- `filter_negative_reads_data_block`: boolean; with a decoded block handle and
  a valid filter returning false, does point lookup still read that data block?
- `out_of_range_filter_may_match`: boolean returned when the requested filter
  region index is outside the filter-block reader's stored region count.
- `user_filter_receives`: `internal_key` or `user_key`, through InternalFilterPolicy.
- `block_cache_key`: array of the two encoded components in order, using
  `block_offset`, `file_number`, and `table_cache_id` as candidate names. Here
  `table_cache_id` means the table object's `cache_id`, not an open-table LRU handle.
- `external_uncompressed_data_cachable`: boolean; on a successful uncompressed
  block read, the file returned storage other than the supplied scratch buffer.
  Is that data marked eligible for an additional block-cache entry?
- `metadata_error_aborts_open`: boolean; after the footer and index block were
  successfully read, does failure to read optional metaindex data fail Table::Open?
- `open_errors_cached`: boolean; does TableCache retain failed table-open results?
- `crc_includes_compression_byte`: boolean; when verification runs, does the
  block CRC cover the compression-type byte as well as the block's data bytes?

Use point reads, not iterators, compaction, or recovery. Assume valid options,
correctly ordered table files, a live snapshot if supplied, and successful I/O
except the explicitly requested metadata/table-open error cases. For cache
questions assume the relevant cache exists; for filter questions assume a policy
is configured. Do not propose a patch or infer behavior from a newer release.
Do not modify `src/leveldb`. Scratch analysis files elsewhere in `/app` are fine.
No compilation, dependency installation, or network access is required.
