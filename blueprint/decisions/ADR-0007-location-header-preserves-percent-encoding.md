# ADR-0007 — Location header preserves percent-encoding, not raw bytes

**Status:** Accepted

## Context

`../GUARANTEES.md`'s "Round-trip integrity" guarantee originally stated that
the redirect `Location` header reproduces `original_url` exactly — "no
normalization, trailing-slash addition/removal, or percent-encoding
changes." A security audit found this doesn't hold in practice:
`src/url_shortener/redirect.py` uses `fastapi.responses.RedirectResponse`,
which percent-encodes characters outside a defined safe set (via
`urllib.parse.quote()`) before writing the `Location` header. An
`original_url` containing a space, a quote character, or a non-ASCII/IDN
host is stored unmodified but comes back percent-encoded in the `Location`
header — a real, demonstrable mismatch with the guarantee's literal wording.

## Decision

The `Location` header reproduces `original_url` as its RFC 3986
percent-encoding-equivalent representation, not necessarily byte-for-byte.
Characters requiring encoding for safe HTTP header transport (spaces,
quotes, non-ASCII, etc.) are percent-encoded; this is standard, correct
HTTP behavior, and any client dereferencing the redirect resolves to the
identical resource. `../GUARANTEES.md` is updated to reflect this.

## Alternatives considered

- **Manually construct the `Location` header to preserve the original
  string as literal bytes.** Rejected: HTTP header values are restricted to
  a safe byte range; forcing literal non-ASCII/control bytes into a header
  either violates the HTTP spec outright or reopens exactly the
  CRLF-header-injection risk that motivated adopting `RedirectResponse` in
  the first place (see the control-character validation rule already in
  `../specs/url-creation.md`, and the prior fix that replaced a raw
  `Response(headers=...)` construction with `RedirectResponse` specifically
  to close that gap).
- **Restrict `original_url` at creation time to only ASCII-safe,
  unencoded-transportable characters.** Rejected: overly restrictive for a
  general-purpose URL shortener; would reject many legitimate URLs (any
  non-ASCII/IDN host, query strings with spaces or special characters) that
  browsers handle correctly today via percent-encoding.

## Consequences

`../GUARANTEES.md`'s round-trip guarantee is now precise about what
"preserved" means (encoding-equivalent, not byte-identical) for the
`Location` header specifically — the metadata endpoint's JSON
`original_url` field is unaffected by this ADR and continues to return the
exact stored string (JSON string encoding, not HTTP header encoding,
applies there — no percent-encoding occurs in a JSON response body).
