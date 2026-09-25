# Inventory the impact of a shared signing helper

Before changing `django.utils.crypto.salted_hmac`, we need a source-backed
inventory of code that can reach it. This is a read-only dependency audit, not a
request to change cryptography or repair Django.

The pinned Django Python source is in `/app/src/django`; dependencies are in
`/app/vendor`. Analyze this version, not a newer installed release.

Write `/app/src/impact-inventory.json` with:

1. `direct_callers`: every direct call site of `salted_hmac` anywhere in the
   supplied Django source. Each item is `{"caller": "file.py:Qualified.symbol",
   "line": 123}`. Imports, docstrings, and transitive callers are not call sites.
2. `entrypoints`: an object containing every key from `/app/src/entrypoints.json`.
   For each, report `{"affected": true, "path": ["file.py:Caller", ...,
   "django/utils/crypto.py:salted_hmac"], "call_lines": [123, ...]}` if it can
   reach the helper. Supply a **shortest path by number of direct call edges**,
   not a list of all reachable functions. Otherwise report
   `{"affected": false, "path": [], "call_lines": []}`.

Paths start at the catalog's entrypoint. Each consecutive pair must be a real
caller/callee relationship; `call_lines[i]` locates that call in `path[i]`.
Any physical line within the call expression is acceptable. Use paths relative
to `/app/src`, a colon, and the symbol's defining class/function name. For
inherited methods, name the implementation's defining class, not the receiving
subclass. Keep intermediate implementations, including overrides and `super()`
calls. Do not insert factories as callers of methods invoked on their return
values. Ordering of direct callers and JSON object keys does not matter.

Analyze normal valid inputs, including successful verification, with these
bindings (not arbitrary application extensions):

- `SIGNING_BACKEND = django.core.signing.TimestampSigner`; Django's standard
  JSON serializers and default password-reset token generator.
- Users are Django's standard `auth.User`, using its inherited implementations;
  authentication uses `django.contrib.auth.backends.ModelBackend`.
- Sessions are `django.contrib.sessions.backends.signed_cookies.SessionStore`.
  Session data is already loaded into memory before an entrypoint is called.
- Passwords use Django's `PBKDF2PasswordHasher`, with current-format hashes.
- No custom subclasses, monkeypatches, serializers, model fields, signal
  receivers, or password validators. Do not include hypothetical caller-supplied
  callbacks, implicit property/dunder dispatch, or a later middleware request.

“Affected” means the implementation can call this exact helper in this scope;
it does not mean every input takes that branch, and does not mean every API
using hashes, random tokens, or constant-time comparison is affected.

Use any available inspection tools. Do not modify the supplied Django source,
dependencies, license, or entrypoint catalog. Scratch analysis files outside
those protected paths are allowed. The output must be a regular UTF-8 JSON file
smaller than 64 KiB, without duplicate keys, comments, or additional fields.
