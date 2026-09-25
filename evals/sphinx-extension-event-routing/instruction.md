# Audit extension event routing before changing the documentation pipeline

We need an exact event-listener inventory for the frozen Sphinx application
configuration in `/app/src/profile.json`. Use the source under `/app/src/sphinx`
to determine the callbacks registered for every event listed in that profile.

The observation point is **immediately after a fresh `Sphinx` HTML application
finishes initialization, before any document build starts**. Include Sphinx's
default extensions, dependencies loaded by the configured extensions, and
registered environment collectors—not just the four explicitly enabled
extensions. A callback stays in the inventory even if its body would do nothing
for the HTML builder. Conversely, an event name or callback appearing in source
does not prove it is registered for this configuration.

Write `/app/src/event-routing.json`:

```json
{
  "events": {
    "some-event": [
      {"handler": "sphinx/path/to/module.py:Class.method", "priority": 500}
    ]
  }
}
```

Include every requested event, using an empty list if it has no listeners.
Within each event, put listeners in their actual dispatch order: increasing
priority, then registration order when priorities tie. Identify a handler by its
defining file relative to `/app/src`, a colon, and its qualified function/method
name. For nested functions, both `setup.<locals>.callback` and `setup.callback`
are accepted. For bound methods, use the defining class, not an instance ID.
Do not invent listener IDs or include event documentation as a callback.

The minimal document directory is `/app/src/project`. Use a fresh application,
no saved environment, no extra configuration file, and only the overrides in
the profile; output/doctree directories may be temporary. All dependencies are
available under `/app/vendor`. Analysis scripts, runtime inspection, and available
repository tools are permitted. Do not modify frozen source, dependencies,
profile, or input documents. No build or network access is needed for this audit.
