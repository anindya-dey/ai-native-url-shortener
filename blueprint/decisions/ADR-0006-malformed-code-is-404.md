# ADR-0006 — A malformed code returns 404, not 422

**Status:** Accepted

## Context

`../contracts/openapi.yaml` constrains the `{code}` path parameter to
`^[A-Za-z0-9]{7}$` for both `GET /{code}` and `GET /api/v1/urls/{code}`.
Nothing previously specified what happens when a request's path segment
doesn't match that shape at all — e.g. `GET /ab` (too short) or
`GET /toolongcode123` (too long, wrong characters). A reasonable
alternative implementation might reject these with `422` (malformed input)
before ever checking whether a matching record exists.

## Decision

A path segment that doesn't match `^[A-Za-z0-9]{7}$` is treated identically
to a well-formed code that doesn't exist: `404` with
`{ "detail": "Short URL not found" }`. There is no separate malformed-input
response for this parameter.

## Alternatives considered

- **Return 422 for a shape mismatch, 404 for a shape match with no
  record.** Rejected: this distinction leaks information about the exact
  validation rule (code length and charset) to any caller probing the
  endpoint, for no benefit to legitimate clients — a legitimate client
  always has a `code` from a real `ShortUrl` response, which is always
  well-formed by construction. Collapsing both cases to `404` is the more
  defensive choice and requires no separate error path.

## Consequences

`../specs/redirects.md` and `../specs/metadata.md` both need to state this
explicitly rather than leaving it implicit. Implementations should perform
the shape check and the existence check as one indistinguishable failure
mode, not as two sequential checks with different responses — a shape
check that short-circuits to `404` before ever querying storage is
consistent with this decision and likely the simplest implementation.
