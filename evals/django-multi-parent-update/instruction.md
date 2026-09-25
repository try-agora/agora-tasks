# Bulk updates corrupt unrelated parent records

An application using Django models with multiple concrete parents reports that
`QuerySet.update()` changes unrelated rows in a parent table while leaving the
intended objects unchanged. It happens when the parent tables have independently
allocated primary keys; basic examples with coincidentally equal keys pass.

Repair the underlying ORM behavior in `/app/src/django`. Updates through children
and deeper descendants must target the actual associated parent rows, including
when an update changes fields in several tables or its filter uses inherited
fields. Do not change unrelated rows or fields. Preserve expressions, the return
value, empty querysets, transactions, and ordinary single-parent/single-table
updates. Keep updates set-based: do not replace a bulk operation with per-object
`save()` calls or SQL statements proportional to the number of matched objects.

`python /app/smoke.py` reproduces one affected case. The fixture contains the
upstream Python library source plus its local runtime dependencies. SQLite is
available; no external service or package download is necessary.

Edit the library source, not the reproduction or dependencies. Leave the repair
in the working tree. Any available navigation tools are optional; correctness
depends only on observable database behavior, not which tool you use.
