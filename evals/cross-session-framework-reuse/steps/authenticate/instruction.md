The source workspace has been restored to its original baseline. Implement this independently of the previous feature.

Add optional authentication to Microapp through its registered middleware extension point.
When config.DEFAULTS["auth_required"] is true, reject requests without a nonblank
Authorization header with status 401. Header names are case-insensitive. Presence is
the contract here: token cryptography is outside this fixture. When false, preserve
anonymous access. Authorized requests retain normal routing; logging must still wrap
every request, including rejected ones. Do not mutate caller-owned headers.
Keep the existing App.handle interface. Run the public tests and add your own checks.
