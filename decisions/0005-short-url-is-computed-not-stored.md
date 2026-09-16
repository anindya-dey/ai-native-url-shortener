# 0005 — short_url is computed at read time, not stored

**Status:** Accepted

## Context

Every `ShortUrl` response includes `short_url`, the fully qualified,
redirectable URL. Nothing previously specified where its host/scheme came
from, or whether it was stored alongside the record at creation time or
derived on every read. Both are plausible: storing it avoids
recomputation; deriving it avoids staleness.

## Decision

`short_url` is computed on every read as `{BASE_URL}/{code}`, where
`BASE_URL` is a single, fixed value from external configuration (e.g. an
environment variable), never derived from the incoming request (not from
the `Host` header). It is never stored as a literal string alongside the
record — only `code` is persisted, and `short_url` is reconstructed from
`code` plus whatever `BASE_URL` is configured at the time of the read.

## Alternatives considered

- **Store `short_url` as a literal at creation time.** Rejected: if
  `BASE_URL` ever changes (new domain, moved deployment), every previously
  stored `short_url` would be silently wrong until a data migration
  rewrote them all. Computing at read time makes a `BASE_URL` change take
  effect immediately for every existing record, with no migration.
- **Derive the base URL from the request's `Host` header.** Rejected: this
  was the other option surfaced during review. It's more flexible for
  multi-domain deployments, but introduces a real security consideration
  (Host header can be spoofed unless validated against an allowlist) and
  makes the guarantee in `../GUARANTEES.md` ("short_url
  construction") harder to test deterministically, since the expected
  value would depend on how a test client sets its Host header rather than
  on a single configured constant.

## Consequences

The implementation needs exactly one piece of configuration (`BASE_URL`)
that every module constructing a `ShortUrl` response reads from — this
does not change `../MODULE_BOUNDARIES.md`'s ownership model, since `BASE_URL`
is global configuration, not data any module writes. If multi-domain
support is ever required, this decision should be revisited alongside the
Host-header alternative rejected above, and `../GUARANTEES.md`'s
"short_url construction" properties will need updating to match.
