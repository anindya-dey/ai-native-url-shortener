# Shared conventions

These rules apply across every endpoint. Individual specs reference this
file rather than repeating these rules.

## Field naming

JSON payloads use: `original_url`, `short_url`, `code`, `click_count`,
`created_at`, `expires_at`. See the `ShortUrl` schema in
`../contracts/openapi.yaml` for the authoritative shape.

## Time handling

- All timestamps are UTC, ISO 8601 (e.g. `2026-09-16T12:00:00Z`).
- If a caller submits a naive (timezone-less) timestamp for `expires_at`, it
  is interpreted as UTC.
- All stored and returned timestamps are UTC, regardless of input timezone.

## Errors

- Validation failures return `422` with a `detail` field describing what
  failed. See the `ValidationError` schema in `../contracts/openapi.yaml`.
- Requests referencing an unknown code return `404` with
  `{ "detail": "Short URL not found" }`.
- Requests referencing a code that exists but has expired are handled
  per `expiration.md` — expiration is not the same as "not found."

## Identifiers

- Codes are exactly seven characters from a fixed charset defined in
  `url-creation.md`.
- Codes are case-sensitive and treated as opaque identifiers by callers.

## Configuration

This system requires exactly one piece of external configuration:

- **`BASE_URL`** — an absolute URL (`http` or `https`) with no trailing
  slash, used to construct `short_url` values as `{BASE_URL}/{code}`. See
  `url-creation.md` and `../decisions/0005-short-url-is-computed-not-stored.md`.
  Required at startup; there is no default. How it's supplied (environment
  variable, config file, secrets manager) is an implementation choice, not
  a spec requirement — only the name `BASE_URL` and its constraints
  (absolute URL, no trailing slash) are part of the contract other tooling
  or documentation should assume.
