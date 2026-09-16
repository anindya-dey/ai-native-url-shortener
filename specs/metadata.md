# Metadata

## Contract

`GET /api/v1/urls/{code}` — see `../contracts/openapi.yaml`. Returns the
`ShortUrl` resource for the given code without redirecting and without
affecting `click_count`.

## Business rules

- Returns the full `ShortUrl` resource (see the `ShortUrl` schema in
  `../contracts/openapi.yaml`) for an existing code, regardless of whether
  it has expired.
- Looking up metadata never increments `click_count` — only a redirect
  (`GET /{code}`) does that. This endpoint is read-only with respect to
  click tracking.
- A request for a code that does not exist returns `404` with
  `{ "detail": "Short URL not found" }`.
- A request whose path segment doesn't match the code shape
  (`^[A-Za-z0-9]{7}$`) returns the same `404` — see
  `../decisions/ADR-0006-malformed-code-is-404.md`.
- Expired short URLs are still returned by this endpoint (the caller can
  see that a code exists and is expired); only the redirect endpoint
  changes behavior on expiration. See `expiration.md`.

## Acceptance criteria

```gherkin
Scenario: Metadata for an active short URL
  Given an existing, unexpired short URL with code "abc1234"
  When the client GETs /api/v1/urls/abc1234
  Then the response status is 200
  And the response body matches the ShortUrl schema
  And click_count for "abc1234" is unchanged by this request

Scenario: Metadata for an expired short URL is still retrievable
  Given an existing short URL with code "abc1234" that expired 1 hour ago
  When the client GETs /api/v1/urls/abc1234
  Then the response status is 200
  And the response body's expires_at is in the past

Scenario: Metadata for unknown code returns 404
  Given no short URL exists with code "zzzzzzz"
  When the client GETs /api/v1/urls/zzzzzzz
  Then the response status is 404

Scenario: Malformed code returns 404, not 422
  Given no prior state
  When the client GETs /api/v1/urls/ab
  Then the response status is 404
```

See `../features/metadata.feature` for the executable form.
