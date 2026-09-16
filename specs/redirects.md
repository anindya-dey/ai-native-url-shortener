# Redirects

## Contract

`GET /{code}` — see `../contracts/openapi.yaml`. Not under `/api/v1`; this
is the public-facing redirect path, distinct from the API namespace.

## Business rules

- A request for an existing, unexpired code returns an HTTP redirect
  (`302`) with `Location` set to the record's `original_url`.
- A request for a code that does not exist returns `404` with
  `{ "detail": "Short URL not found" }`.
- A request whose path segment doesn't match the code shape
  (`^[A-Za-z0-9]{7}$` — wrong length or invalid characters) returns the
  same `404` as a well-formed but nonexistent code. There is no separate
  malformed-input response for this parameter — see
  `../decisions/0006-malformed-code-is-404.md`.
- A request for a code that exists but has expired is handled per
  `expiration.md` (not treated identically to "not found").
- Each successful redirect increments `click_count` for that code by
  exactly `1`. A request that results in `404` or an expiration response
  does not change `click_count`.
- `click_count` increments are atomic — concurrent redirect requests for
  the same code must not lose increments (see
  `../GUARANTEES.md`).

## Acceptance criteria

```gherkin
Scenario: Redirect to an active short URL
  Given an existing, unexpired short URL with code "abc1234"
  And original_url "https://example.com/target"
  When the client GETs /abc1234
  Then the response status is 302
  And the response Location header equals "https://example.com/target"
  And click_count for "abc1234" increases by 1

Scenario: Unknown code returns 404
  Given no short URL exists with code "zzzzzzz"
  When the client GETs /zzzzzzz
  Then the response status is 404
  And the response body's detail equals "Short URL not found"
  And no click_count is modified

Scenario: Malformed code returns 404, not 422
  Given no prior state
  When the client GETs /ab
  Then the response status is 404
  And the response body's detail equals "Short URL not found"

Scenario: Concurrent redirects do not lose click count
  Given an existing, unexpired short URL with code "abc1234"
  And click_count currently at 0
  When 10 redirect requests for "abc1234" are made concurrently
  Then click_count for "abc1234" equals 10
```

See `expiration.md` for the expired-code case and
`../features/redirects.feature` for the executable form of
these scenarios.
