# Expiration

## Business rules

- `expires_at` is optional at creation. A short URL with no `expires_at`
  never expires.
- At creation time, a submitted `expires_at` must be strictly in the future
  relative to the request-processing time, per `url-creation.md`. This is
  the only point at which expiration is validated against the clock —
  once created, a record with a past `expires_at` (because time has since
  passed) is valid and simply "expired," not invalid.
- A naive (timezone-less) `expires_at` submitted at creation is interpreted
  as UTC, per `shared-conventions.md`.
- Expiration is evaluated at request time by comparing `expires_at` to the
  current UTC time, not cached or precomputed at creation.

## Effect of expiration by endpoint

- `GET /{code}` (redirect): an expired code returns `410` with
  `{ "detail": "Short URL has expired" }`, and does not increment
  `click_count`. This is distinct from `404` — the code is known, but no
  longer redirectable.
- `GET /api/v1/urls/{code}` (metadata): an expired code still returns `200`
  with the full resource, per `metadata.md`. The caller can inspect
  `expires_at` to determine expiration status themselves.
- `POST /api/v1/urls` (creation): rejects a past `expires_at` outright, per
  `url-creation.md`. This is a creation-time validation only.

## Boundary condition

- A short URL expires at exactly `expires_at`, inclusive. A redirect
  request at exactly `expires_at` is treated as expired (the boundary
  belongs to "expired," not "active").

## Acceptance criteria

```gherkin
Scenario: Redirect to an expired short URL
  Given an existing short URL with code "abc1234"
  And expires_at set to 1 hour in the past
  When the client GETs /abc1234
  Then the response status is 410
  And the response body's detail equals "Short URL has expired"
  And click_count for "abc1234" is unchanged

Scenario: Redirect at the exact expiration boundary is treated as expired
  Given an existing short URL with code "abc1234"
  And expires_at set to exactly the current request time
  When the client GETs /abc1234
  Then the response status is 410

Scenario: A short URL with no expires_at never expires
  Given an existing short URL with code "abc1234" and no expires_at
  When the client GETs /abc1234 at any future time
  Then the response status is 302
```

See `../acceptance/features/expiration.feature` for the executable form.
