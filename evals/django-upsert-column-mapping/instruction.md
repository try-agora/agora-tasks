# Bulk upserts fail on models with custom database columns

Our importer calls `QuerySet.bulk_create(update_conflicts=True, ...)` using model
field names, as the ORM API expects. Ordinary inserts work, but updating conflicts
fails or targets the wrong identifiers when those fields have custom `db_column`
values. The incoming records may mix new and existing rows.

Repair this behavior in `/app/src/django`. Both the conflict target and the fields
being updated must use the correct physical columns in generated SQL. Support
single and compound unique targets, primary-key targets (including the `pk`
alias), and concrete foreign-key fields. Preserve batching, atomicity, parameter
binding, untouched fields/rows, empty input, ordinary inserts, ignored conflicts,
and rejection of unsupported update fields. Keep the operation set-based; do not
replace bulk creation with per-row queries or `save()` calls.

`python /app/src/reproduce.py` demonstrates one failure using SQLite. All library
source and runtime dependencies are available locally; no network or additional
services are needed. Edit library source, not the reproduction or dependencies,
and leave the repair in the working tree. Any available navigation tools are
optional; grading checks database outcomes, not patch shape or tool choice.
