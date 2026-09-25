# Prioritize shared utility changes by caller fan-in

Before scheduling compatibility reviews, rank the ten helper functions listed in
`/app/src/helpers.json` by the number of distinct Django Python source files that
directly call them. The frozen repository is under `/app/src/django`.

Write `/app/src/helper-fan-in.json`:

```json
{
  "ranking": [
    {"helper": "django.utils.some_module.some_function", "caller_file_count": 12}
  ]
}
```

Include every listed helper exactly once. Sort by decreasing distinct-file count,
breaking ties by increasing helper identifier. Count only files under `django/`;
exclude vendored dependencies and any analysis scripts you create. A file counts
once even if several functions or call sites within it invoke the helper. Calls
inside the helper's own module count too.

This is a **source-level explicit-call inventory**, not a runtime coverage or
transitive-reachability estimate. Include explicit `f(...)` call expressions
inside conditional branches, class bodies, methods, and functions, irrespective
of whether a branch runs on this machine. Resolve imported aliases and module
qualifiers to the defining helper; an unrelated same-named function is not that
helper. Imports, comments, string mentions, and bare decorator/callback references
without a call expression do not themselves count. Repeated call sites do not
increase a file's weight.

Do not modify the frozen source, dependencies, or helper catalog. The artifact is
a review-prioritization input, so completeness and exact counts matter. Source
inspection, scripts, and available repository tools are all acceptable; no
network access is required.
