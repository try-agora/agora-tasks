# Audit Nest's HTTP lifecycle before changing request policy

A team is moving validation and access policy into shared framework hooks. Map
the **existing** Nest HTTP implementation in `/app/src/packages` so reviewers can
choose the right boundary and avoid changing unrelated transports. The frozen
snapshot is Nest 10.4.15. Use its Express adapter, not Fastify, WebSockets, RPC,
GraphQL, or the similarly named external-context helpers.

The navigation endpoints are `RouterExplorer` (route wiring) and
`ExpressAdapter.reply` (ordinary response delivery). Explain the source path
between them, including the guard, pipe, interceptor, and exception boundaries
specified below; merely locating those two endpoints is not sufficient.

Write `/app/src/http-lifecycle.json` with exactly two objects, `locations` and
`decisions`. Each location is `{"file": "packages/...ts", "symbol":
"Class.method", "line": 42}`. Paths are relative to `/app/src`. The line is the
first line of the decisive expression described below, **not** the method's
declaration. For an anonymous callback, name its enclosing class method.

Include these location keys:

| Key | Decisive expression to locate |
| --- | --- |
| `route_metadata` | Read the method's path metadata from its prototype callback. |
| `route_registration` | Register the final path and handler through the selected router method. |
| `request_scope` | Load a request-scoped controller instance through the injector. |
| `guard_call` | Invoke an individual guard's `canActivate`. |
| `guard_rejection` | Convert a false guard result into the HTTP forbidden exception. |
| `interceptor_call` | Invoke the current interceptor with its continuation handler. |
| `body_parameter` | Extract a named or whole body from the HTTP request. |
| `parameter_pipes` | Concatenate the shared pipes with the parameter's pipes. |
| `pipe_call` | Invoke an individual pipe's `transform`. |
| `controller_call` | Invoke the controller callback with the assembled arguments. |
| `observable_result` | Convert an ordinary Observable handler result to its final value. |
| `adapter_reply` | Delegate an ordinary result to the configured HTTP adapter's reply. |
| `express_body` | Choose Express JSON output versus string output for a non-stream body. |
| `exception_boundary` | Forward a rejected route callback to its exception handler. |
| `filter_precedence` | Install custom HTTP filters in their final precedence order. |
| `filter_dispatch` | Invoke the selected custom exception filter. |
| `fallback_exception` | Send an unhandled HTTP exception through the adapter when headers are unsent. |

Also derive these `decisions` from the same pinned source:

- `guard_denial`: string exception class name used for a false guard result.
- `guard_short_circuits`: boolean; does one false guard prevent later guards?
- `pipe_scope_order`: array using `global`, `controller`, `method`, `parameter`,
  in the application order for one ordinary pipeable argument.
- `pipes_for_one_argument`: `sequential` or `parallel`.
- `different_arguments`: `sequential` or `parallel` (how resolutions are awaited).
- `interceptor_can_skip_controller`: boolean; can an interceptor return its own
  result without invoking its continuation and therefore skip the controller?
- `ordinary_observable_value`: `first`, `last`, or `all`.
- `post_default_status`: integer status without an explicit status decorator.
- `response_decorator_auto_reply`: boolean; ordinary `@Res()` with no passthrough.
- `passthrough_auto_reply`: boolean; ordinary `@Res({passthrough: true})`.
- `filter_scope_order`: array using `global`, `controller`, `method`, in search
  order when exactly one applicable filter exists at each scope.
- `all_matching_filters_run`: boolean; do all matching custom filters execute?

For ordinary responses, exclude render, redirect, SSE, streams, custom headers,
and `@Next()`. Assume providers exist and the handler returns a valid result.
Report framework behavior, not a proposed policy or behavior from a newer release.
Do not change the frozen `packages/`, license, or configuration files. Scratch
analysis scripts beside them are fine. No dependency installation or network
access is needed for this source audit.
