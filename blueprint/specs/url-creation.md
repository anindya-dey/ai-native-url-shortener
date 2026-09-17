# URL creation

## Contract

`POST /api/v1/urls` — see `../contracts/openapi.yaml` for the full request
and response schema. Request carries `original_url` (required) and
`expires_at` (optional). Response is a `ShortUrl` resource with HTTP `201`.

## Business rules

- Only `http` and `https` schemes are accepted for `original_url`.
- `original_url` must include a non-empty host. A scheme with no host (e.g.
  `https://` alone) is rejected.
- `original_url` must not contain control characters (`\r`, `\n`, or other
  C0/C1 control characters) anywhere in the string. Such values are
  rejected.
- `original_url` is at most 2048 characters. Longer values are rejected.
- `expires_at` is optional. When present, it must be strictly in the future
  relative to the time the request is processed.
- The service generates a seven-character code from a fixed charset
  (`[A-Za-z0-9]`, no ambiguity exclusions required) that is collision-safe
  against existing active codes.
- On creation, `click_count` starts at `0` and `created_at` is set to the
  current UTC time.
- A generated code that collides with an existing record is regenerated and
  retried. An existing record is never overwritten as a result of a
  collision.
- `short_url` is computed as a fixed, externally configured base URL
  (`BASE_URL`) joined with the code — `{BASE_URL}/{code}` — never stored as
  a literal value and never derived from the incoming request. It is
  recomputed from `code` and the current `BASE_URL` on every response, so a
  future change to `BASE_URL` is reflected immediately for all existing
  records without a data migration. See `../decisions/ADR-0005-short-url-is-computed-not-stored.md`.
- No deduplication is performed. Submitting the same `original_url` more
  than once creates a new, independent record and code each time; the
  service never looks up or returns a previously generated code for a
  matching `original_url`.

## Acceptance criteria

```gherkin
Scenario: Valid destination creates a short URL
  Given a request with original_url "https://example.com/a/long/path"
  And no expires_at
  When the client POSTs to /api/v1/urls
  Then the response status is 201
  And the response body's original_url equals "https://example.com/a/long/path"
  And the response body's code is 7 characters
  And the response body's click_count equals 0

Scenario: Valid destination with a future expiration
  Given a request with original_url "https://example.com"
  And expires_at set to a timestamp 1 hour in the future
  When the client POSTs to /api/v1/urls
  Then the response status is 201
  And the response body's expires_at equals the submitted timestamp, in UTC

Scenario: Unsupported scheme is rejected
  Given a request with original_url "ftp://example.com/file"
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: Malformed URL is rejected
  Given a request with original_url "not a url"
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: Oversized original_url is rejected
  Given a request with original_url longer than 2048 characters
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: Scheme-only URL with no host is rejected
  Given a request with original_url "https://"
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: original_url containing control characters is rejected
  Given a request with original_url containing a carriage return or line feed character
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: Past expiration is rejected
  Given a request with original_url "https://example.com"
  And expires_at set to a timestamp 1 hour in the past
  When the client POSTs to /api/v1/urls
  Then the response status is 422

Scenario: Code collision is retried, not overwritten
  Given an existing short URL record with code "abc1234"
  And the code generator would produce "abc1234" on its first attempt
  When a new request is POSTed to /api/v1/urls
  Then the service retries generation until a non-colliding code is produced
  And the existing record for "abc1234" is unchanged
  And the response status is 201 with a different code

Scenario: short_url is built from the configured base URL and the code
  Given the configured BASE_URL is "https://short.example"
  When the client POSTs to /api/v1/urls with original_url "https://example.com"
  Then the response body's short_url equals "https://short.example/" followed by the response body's code

Scenario: Submitting the same original_url twice creates two independent codes
  Given a request with original_url "https://example.com/same"
  When the client POSTs to /api/v1/urls twice with the same original_url
  Then both responses have status 201
  And the two responses have different codes
```

See `../features/url-creation.feature` for the version of these
scenarios an agent should treat as the executable acceptance target, and
`../GUARANTEES.md` for guarantees (e.g. code uniqueness) that
apply beyond these specific examples.
