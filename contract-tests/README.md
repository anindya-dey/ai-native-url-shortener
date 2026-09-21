# Contract tests

A black-box HTTP test suite that knows nothing about which implementation
it's running against — no imports from `python/`, `typescript/`, or
`rust/`, no assumptions about language or framework. It only knows
`../blueprint/contracts/openapi.yaml`, `../blueprint/features/*.feature`,
and `../blueprint/GUARANTEES.md`. It talks to a running server purely
over HTTP.

This is the actual proof behind this repo's central claim: the same
unmodified test file passes against Python, TypeScript, and Rust, because
none of them differ in behavior — only in the code that produces it.

## Running it against one implementation

1. Start the implementation you want to test, with its `BASE_URL` set to
   wherever it'll be reachable — e.g. for Python:

   ```bash
   cd python && BASE_URL=http://127.0.0.1:8000 uv run uvicorn url_shortener.main:app --port 8000
   ```

2. In another terminal, from this directory:

   ```bash
   uv sync
   TARGET_URL=http://127.0.0.1:8000 uv run pytest -q
   ```

`TARGET_URL` must equal the server's own `BASE_URL` — this suite asserts
that returned `short_url` values equal `{TARGET_URL}/{code}`, which is
only true if both point at the same address.

Swap step 1 for `typescript/` (`BASE_URL=... npm start`, see
`../typescript/README.md`) or `rust/` (`BASE_URL=... cargo run`, see
`../rust/README.md`) to run the identical suite against either of those
instead — nothing in step 2 changes.

## Running it against all three at once

```bash
./run-all.sh
```

Starts each implementation in turn on its own port, points this suite at
it, runs the full suite, tears the server down, and moves to the next.
Prints a pass/fail summary for all three at the end. This is the closest
thing in this repo to a single command that demonstrates the whole
thesis: one test file, three unrelated tech stacks, identical results.

## What's deliberately not covered here

A few `blueprint/GUARANTEES.md` and `blueprint/features/` scenarios can't
be forced from outside the process over plain HTTP:

- **"Code collision is retried, not overwritten"** requires stubbing the
  code generator to force a specific collision — each language's own
  test suite injects this internally (e.g.
  `rust/tests/url_creation.rs::code_collision_is_retried_not_overwritten`).
- **"Changing `BASE_URL` and re-reading an existing record reflects the
  new value immediately"** requires reconfiguring and restarting the live
  server mid-test, which this suite doesn't attempt.
- **Exact-instant expiration boundary tests** substitute a near-boundary
  wait (create with a short future `expires_at`, sleep past it, assert
  expired) instead of controlling the server's clock directly, since a
  black-box client can't inject a frozen clock the way each language's
  own unit tests do.

These gaps are covered by each language directory's own test suite, not
missing from verification entirely — just not reproducible from this
vantage point. See each language's `tests/` (or `python/tests/`) for the
internal versions.
