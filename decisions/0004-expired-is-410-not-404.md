# 0004 — Expired short URLs return 410, not 404

**Status:** Accepted

## Context

`../specs/expiration.md` and `../specs/redirects.md` distinguish "code
never existed" (`404`) from "code existed but has expired" (`410`). It
would be simpler to treat both as `404`.

## Decision

A redirect request for a code that exists but has expired returns
`410 Gone`, distinct from `404 Not Found` for a code that never existed.

## Alternatives considered

- **Collapse both cases into 404.** Rejected: `404` tells a caller "this
  never existed or isn't yours to know about," while `410` tells a caller
  "this existed and is gone on purpose" — a meaningfully different signal
  for any client or monitoring system trying to distinguish "bad link"
  from "expected expiration." Collapsing them would also make it
  impossible to write the `../acceptance/features/expiration.feature`
  scenarios as distinct, checkable cases.

## Consequences

The metadata endpoint (`../specs/metadata.md`) deliberately does *not* mirror
this distinction — it returns `200` for expired codes so a caller can
inspect `expires_at` directly, rather than getting a `410` with no data.
Any future client-facing documentation should explain the 404/410
distinction explicitly, since it's easy for API consumers to conflate them.
