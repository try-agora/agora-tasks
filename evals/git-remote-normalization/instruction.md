Repair parse_remote(value) in src/remotes.py. Return exactly these fields:
transport ("ssh" or "https"), lowercase host, integer port, user (string or None),
and repository path without surrounding slashes or a terminal ".git".
Support absolute ssh:// and https:// URLs and SCP-style [user@]host:path.
Preserve nested repository paths and explicit ports, including bracketed IPv6 URL hosts.
Default ports are 22 and 443. SCP syntax always means SSH, never host:port.
Raise ValueError for local paths, empty/non-string inputs, any whitespace, unsupported
schemes, embedded passwords, invalid ports, query strings, fragments, and repository
paths containing empty, "." or ".." components. No network access is needed.
