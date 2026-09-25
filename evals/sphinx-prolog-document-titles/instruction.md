# Shared RST prologs make document titles disappear

A documentation project injects shared substitutions through `rst_prolog`.
Documents whose first heading begins with an inline role lose their title in
the rendered page and navigation tree. Turning off the prolog makes the title
reappear, but then shared substitutions stop working. Plain headings work.

Repair the underlying Sphinx behavior in `/app/src/sphinx`. Keep role-based
headings intact while still applying the prolog. Existing document metadata and
valid leading field lists—including multi-word and escaped field names—must
remain before the prolog. Preserve source locations of original input lines,
ordinary headings, no-prolog behavior, and epilogs. The fix must not be specific
to one role, heading text, project, or renderer.

The fixture contains the pinned Sphinx source, its runtime resources, and local
dependencies. You can reproduce with:

```bash
python -m sphinx -b html -q /app/src/demo /app/build-demo
```

The demo's API page should have a title and appear in the index navigation, and
its shared substitution should expand. Fix library source, not the demo or
dependencies. No network or package installation is needed. Leave changes in
the working tree. Use any available navigation tools; correctness is determined
by document processing and rendered output, not tool use or patch similarity.
