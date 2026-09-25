# Audit lookup extension points before an ORM API migration

We are reviewing a proposed change to the `as_sql` and `process_rhs` hooks on
Django lookups. Produce a complete inheritance inventory so reviewers can see
which implementations each core lookup would actually dispatch to.

The frozen source is under `/app/src/django`. Scope this review to classes
**defined in `django/db/models/`**, not contrib packages or vendored libraries.
Include every strict descendant of `django.db.models.lookups.Lookup`, including
abstract/intermediate descendants. Exclude `Lookup` itself. Registration is not
a requirement: unregistered descendants still belong in the inventory. A class
whose name contains `Lookup` or `Transform` is not necessarily a descendant.

Write `/app/src/lookup-hierarchy.json` with this shape:

```json
{
  "classes": {
    "django/path/to/module.py:SomeLookup": {
      "bases": ["django/path/to/base.py:SomeMixin", "django/path/to/base.py:Parent"],
      "owners": {
        "as_sql": "django/path/to/implementation.py:DefiningClass.as_sql",
        "process_rhs": "django/path/to/implementation.py:DefiningClass.process_rhs"
      }
    }
  }
}
```

Use defining file paths relative to `/app/src`, followed by a colon and the
qualified class/method name. Include **all direct bases in declaration order**,
including non-lookup mixins. For each hook, identify the class that defines the
implementation selected by normal Python method resolution for an instance of
that lookup. An inherited alias is not a defining implementation. Do not follow
`super()` inside the method: we want the first method selected by dispatch.

JSON key order is irrelevant. Do not modify the frozen Django or vendor source.
You may use temporary analysis scripts and any available repository navigation
tools; no particular tool or technique is required. Do not install dependencies
or rely on network access. The source is sufficient for this read-only review.
