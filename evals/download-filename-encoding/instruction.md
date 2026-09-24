Implement attachment_header(filename) in src/downloads.py.
Return an ASCII Content-Disposition value with disposition "attachment" and a quoted
filename parameter. ASCII basenames must round-trip exactly, including quotes,
backslashes, spaces, and semicolons. Non-ASCII names must include a nonempty ASCII fallback
and filename*=UTF-8'' followed by percent-encoded UTF-8 preserving the exact original name.
Reject empty/non-string inputs and every ASCII control character (U+0000–001F, U+007F)
with ValueError. In particular, CR and LF must never enter a response header.
The input is a basename; no path resolution is required.
