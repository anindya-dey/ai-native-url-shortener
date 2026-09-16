# ADR-0003 — Codes are seven characters from [A-Za-z0-9]

**Status:** Accepted

## Context

A short code needs to be short (that's the point of the product) but needs
enough keyspace to make collisions rare as the number of active URLs grows.

## Decision

Codes are exactly 7 characters from `[A-Za-z0-9]` (62 possible characters
per position), giving 62^7 (≈ 3.5 trillion) possible codes, with collisions
handled by retry-on-conflict per `../specs/url-creation.md`.

## Alternatives considered

- **6 characters.** Rejected: 62^6 (≈ 56.8 billion) is still large, but 7
  was chosen to keep collision retries rare at meaningfully large scale
  (tens of millions of active codes) without a specific measured target —
  this margin is a judgment call, not a derived requirement, and is a
  reasonable candidate to revisit if actual scale or collision-retry rates
  are ever measured in production.
- **UUID or hash-derived codes (much longer).** Rejected: defeats the
  purpose of a *short* URL; the product's value proposition depends on the
  code being short enough to read and type.
- **Sequential/incrementing IDs.** Rejected: makes codes guessable and
  enumerable (a caller could discover other users' short URLs by
  incrementing), which is a privacy leak this product doesn't want even
  without a formal auth model.

## Consequences

Fixes the collision math referenced in `../GUARANTEES.md`
("uniqueness while active"). If code length ever needs to change, this
decision and every one of the following hardcoded occurrences of `7`
need to change together: `../specs/overview.md` (glossary),
`../specs/shared-conventions.md`, `../specs/url-creation.md`, and
`../contracts/openapi.yaml` — which hardcodes it twice, once in the
`Code` parameter pattern and once in the `ShortUrl.code` property
pattern.
