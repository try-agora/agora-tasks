Extend src/notify/core.py's build_payload to accept optional keyword-only sender and
category strings. Include each key only when its value is not None; empty strings are
intentional values and must be preserved. Calling build_payload(message) must still
produce exactly {"msg": message}. All existing alert, digest, and scheduler callers
must retain their behavior. Calls supplying metadata positionally must raise TypeError.
Do not introduce shared mutable payload state.
