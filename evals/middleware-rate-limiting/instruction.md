Implement per-client request limits in Microapp using its registered middleware extension point.
Allow exactly config.DEFAULTS["rate_limit"] requests for each client per App instance,
then return status 429. Counts must persist across requests, but not across App instances.
A zero limit blocks every request. The configuration is a nonnegative integer.
Preserve routing, request headers, and the existing logging middleware's before/after events.
Keep the existing App.handle interface. Run the public tests and add your own checks.
