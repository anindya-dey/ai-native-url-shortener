# Module boundaries

How the implementation is expected to be decomposed, and who owns what data.
Use this before writing code, and re-check it whenever a module starts
accreting responsibilities it didn't start with.

Before accepting a module boundary, confirm:

- It can be understood in about ten minutes without a tour of the rest of
  the system.
- It can be verified at its boundary (inputs and outputs) without booting
  everything else.
- It has exclusive ownership of the data it writes — nothing else writes
  the same fields.
- It communicates through the versioned contract in `contracts/`, not
  through shared internals with another module.
- Deleting and rewriting it feels like mild inconvenience, not dread. If it
  causes dread, the boundary is wrong, or acceptance coverage is missing.

## Modules

### URL creation

- **Owns**: generating and persisting new short URL records, including
  collision retry, and validating/normalizing `expires_at` at creation time.
- **Governed by**: `specs/url-creation.md`, `specs/expiration.md` (the
  creation-time validation and naive-timestamp-to-UTC rules only)
- **Contract**: `POST /api/v1/urls` in `contracts/openapi.yaml`
- **Exclusive write authority over**: creation of new records (not updates
  to `click_count`, which belongs to Redirect).
- **Notes**: safe to rewrite independently as long as nothing else inspects
  *how* a code was generated — only that it matches the `ShortUrl` schema
  in `contracts/openapi.yaml`.

### Redirect

- **Owns**: looking up a code, checking expiration, issuing the redirect,
  incrementing `click_count`.
- **Governed by**: `specs/redirects.md`, `specs/expiration.md`
- **Contract**: `GET /{code}` in `contracts/openapi.yaml`
- **Exclusive write authority over**: `click_count`. No other module
  writes this field — this is what makes the concurrency guarantees in
  `acceptance/guarantees.md` checkable against one module instead of
  the whole system.
- **Notes**: the concurrency guarantee (exactly-once increment under
  concurrent requests) is the part most likely to make this module feel
  risky to rewrite. If it does, confirm the acceptance coverage for that
  guarantee is solid before rewriting, not after.

### Metadata

- **Owns**: read-only lookup of a short URL record, expired or not.
- **Governed by**: `specs/metadata.md`
- **Contract**: `GET /api/v1/urls/{code}` in `contracts/openapi.yaml`
- **Exclusive write authority over**: nothing. This module performs no
  writes, which makes it the simplest to rewrite — there's no
  data-ownership question to resolve.
- **Notes**: if rewriting this ever feels risky, something has leaked write
  behavior into it that violates its read-only contract — treat that as a
  bug to fix, not a reason to avoid rewriting.

### Expiration rule

- **Not a separate module** — expiration (`specs/expiration.md`) is a rule
  applied *by* three other modules, not a service of its own:
  - **URL Creation** validates that a submitted `expires_at` is strictly in
    the future, and interprets naive (timezone-less) timestamps as UTC.
  - **Redirect** compares `expires_at` to the current UTC time on every
    request, inclusive of the boundary, and returns `410` if expired.
  - **Metadata** deliberately does *not* apply the boundary check — it
    always returns `200` regardless of expiration status.
  - Listed here because it's cross-cutting: a change to this rule may
    require updating Creation's validation, Redirect's enforcement, or
    both, depending on what changed.

## Deployment granularity

These three modules plus one cross-cutting rule can live in a single
deployable process. This map describes logical boundaries inside the
codebase — separate files or packages are enough to satisfy "isolated,
replaceable, independently verifiable" at this scale. Split into separate
deployable services only if a concrete reason emerges (e.g., Redirect's
traffic and scaling needs diverge sharply from Creation's) — don't split
preemptively.
