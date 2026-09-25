# Audit the route from a queryset to SQLite

Before adding database instrumentation, we need an accurate execution map of
the frozen Django checkout in `/app/src/django`. Similar method names appear
in several backends and compiler subclasses; distinguish the implementations
actually used by `/app/src/scenario.py` from plausible but inactive ones.

This is a read-only source audit, not a bug fix. Submit
`/app/src/execution-path.json`. Do not modify provided source, dependencies,
or `scenario.py`. You may run the scenario, use temporary analysis scripts
outside the library/dependency directories, and use any available navigation
tools. No network or additional packages are needed.

## Artifact contract

Use one JSON object with exactly `scenarios` and `bindings` as its keys.
Source paths are relative to `/app/src`, symbols are class-qualified names
within that file (for example `SomeClass.some_method`), and line numbers are
one-based. This is a factual call-site inventory, not a prose explanation.

`scenarios` must contain all four named operations in `scenario.py`:
`model_first`, `model_cached`, `flat_first`, and `exists_first`. Each value is:

```json
{
  "sql_count": 1,
  "cache_populated": true,
  "path": [
    {"file": "package/module.py", "symbol": "SomeClass.some_method", "call_line": 123},
    {"file": "package/backend.py", "symbol": "DriverWrapper.execute", "call_line": null}
  ]
}
```

The example is schematic, not an answer. For each operation:

- Count the SELECT statements executed by that operation, excluding setup.
- Record whether that operation's queryset has a populated `_result_cache`
  afterwards (including an empty cached list, if applicable).
- Give the **active Django Python call stack at entry to the first SQLite
  cursor wrapper `execute()`**, ordered outermost to innermost. Include every
  active frame whose source is under `src/django`; omit application, standard
  library, and C frames. Do not include earlier calls that already returned.
  A generator counts when its body is active. If no SELECT executes, use `[]`.
- Each nonterminal `call_line` locates the expression advancing to the next
  frame; any physical line within that call expression is accepted. The
  terminal wrapper frame has `call_line: null`.

`bindings` records four dispatch points that a stack alone cannot fully show.
Each value has `file`, `symbol`, `call_line`, and `target` (a fully qualified
Python symbol, including its defining module). Exported names identifying the
same SQLite driver method are equivalent:

1. `compiler_selector`: where the query asks the connection's operations object
   for a compiler; target the concrete selector method.
2. `compiler_class`: where that selector resolves the compiler class; target
   the class actually selected for the scenario's SELECTs.
3. `cursor_factory`: where the shared database wrapper dispatches cursor
   creation to this backend; target the concrete backend method.
4. `driver_execute`: where Django's SQLite cursor wrapper hands this scenario's
   parameterized query to the underlying driver; target the driver method.

Use the existing SQLite configuration (`DEBUG=False`, no execute wrappers).
Keep the artifact below 32 KiB. You are evaluated on source-grounded facts and
behavior, never on which navigation tool you chose or on a preferred tool sequence.
