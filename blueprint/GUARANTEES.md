# Guarantees

Statements that must hold for any implementation, regardless of language,
storage engine, or internal structure. Phrased so each can become a
property-based test (e.g. Hypothesis, fast-check) rather than a single
example. These complement, not replace, the scenarios in `features/`.

## Code generation

- **Uniqueness while active**: no two short URL records that are both
  currently retrievable (via metadata or redirect) share the same `code`.
- **Shape**: every generated `code` matches `^[A-Za-z0-9]{7}$`, with no
  exceptions, for every record ever created.
- **No overwrite on collision**: if code generation collides with an
  existing record, that existing record's fields are byte-for-byte
  unchanged after the collision is resolved.

## Click tracking

- **Monotonic non-negative**: `click_count` for any code never decreases
  and never goes negative.
- **Exactly-once per successful redirect**: for N successful (302)
  redirects of the same code, with no other requests in between,
  `click_count` increases by exactly N — not more (double counting under
  concurrency), not less (lost updates under concurrency).
- **No increment on failure**: a request that results in `404` or `410`
  never changes `click_count` for any code.
- **No increment on metadata read**: any number of `GET
  /api/v1/urls/{code}` requests never changes `click_count`.

## short_url construction

- **Deterministic from code and configuration**: `short_url` always equals
  the current `BASE_URL` joined with `code`, for every record, regardless
  of when that record was created. Changing `BASE_URL` and then reading an
  existing record must reflect the new `BASE_URL` immediately — `short_url`
  is never a stored literal that could go stale.
- **No two records share a short_url while active**: a direct consequence
  of code uniqueness (see "Uniqueness while active" above) plus
  deterministic construction — if two `short_url` values were ever equal
  for two different active records, their `code`s would have to be equal
  too, which uniqueness already forbids.

## Duplicate submissions

- **No implicit deduplication**: submitting the same `original_url` N times
  produces N records with N distinct codes. The service never treats a
  repeated `original_url` as a cache hit or returns a previously issued
  code for it.

## Round-trip integrity

- **Original URL is preserved exactly**: for any short URL created with a
  given `original_url`, every subsequent metadata read reproduces that
  exact string — no normalization, trailing-slash addition/removal, or
  percent-encoding changes. The redirect `Location` header reproduces
  `original_url` as its RFC 3986 percent-encoding-equivalent
  representation (dereferencing to the identical resource), not
  necessarily as an identical byte sequence — see
  `decisions/ADR-0007-location-header-preserves-percent-encoding.md`.
- **Timestamps round-trip in UTC**: for any `expires_at` submitted at
  creation (naive or UTC), the value returned in every later read
  represents the same instant, expressed in UTC.

## Expiration

- **Boundary is inclusive**: a redirect request at exactly `expires_at`
  behaves as expired (410), not active (302), for every code that has an
  `expires_at`.
- **Expiration doesn't affect metadata visibility**: a code that exists
  remains retrievable via metadata (`200`) whether or not it has expired;
  only the redirect endpoint's status code changes.
- **Absence of expires_at means permanence**: a record created without
  `expires_at` returns `302` on redirect at any future time, arbitrarily
  far out, without a separate migration or explicit action.

## Validation

- **Creation-time-only expiration validation**: `expires_at` in the past is
  rejected at creation (`422`); it is never re-validated as "invalid" once
  time has passed and the record already exists — it becomes "expired"
  (410 on redirect), not "invalid."
- **Scheme restriction is exhaustive**: any `original_url` whose scheme is
  not exactly `http` or `https` is rejected at creation, for every scheme
  value, not a hardcoded blocklist of specific alternatives.
- **Length restriction is exhaustive**: any `original_url` longer than 2048
  characters is rejected at creation, for every length beyond that limit,
  not spot-checked against a few long examples.
- **Malformed and missing codes are indistinguishable to the caller**: for
  every path segment that does not match `^[A-Za-z0-9]{7}$`, both
  `GET /{code}` and `GET /api/v1/urls/{code}` return the same `404` a
  well-formed but nonexistent code would return — never a `422` or `400`
  that would reveal the shape requirement.
