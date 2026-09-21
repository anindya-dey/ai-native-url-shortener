# URL Shortener — Rust implementation

One of several implementations of the specs in `../blueprint/`. See the
root `README.md` for how this fits alongside the others, and
`../AGENTS.md` for how to regenerate this implementation from scratch.

## Stack

Axum + Tokio, serde/serde_json (mirroring the `ShortUrl` and
`ValidationError` schemas in `../blueprint/contracts/openapi.yaml`), an
in-memory single-process store guarded by a `std::sync::RwLock`. Test
suite: `cargo test` (integration tests in `tests/`) + proptest
(property-based tests for `../blueprint/GUARANTEES.md` in
`tests/guarantees.rs`).

## Running the service

**Prerequisites**: Rust (stable) and Cargo.

**Setup / build** (from this directory):

```
cargo build
```

**Required config**: `BASE_URL` must be set — an absolute `http`/`https`
URL with no trailing slash, used to build `short_url` values. There is no
default; the service fails fast at startup without it. This is deliberate
(see `../blueprint/specs/shared-conventions.md`), not a bug.

**Run the server**:

```
BASE_URL=https://short.example cargo run
```

Listens on `0.0.0.0:8080`.

**Run the tests**:

```
cargo test
```

**Try it**:

```
curl -X POST "http://localhost:8080/api/v1/urls" \
  -H 'content-type: application/json' \
  -d '{"original_url": "https://example.com/some/page"}'

curl "http://localhost:8080/api/v1/urls/<code>"   # metadata
curl -i "http://localhost:8080/<code>"            # redirect
```

See `../blueprint/contracts/openapi.yaml` for the full request/response
shapes.

## Status

All three modules (URL creation, Redirect, Metadata) are implemented. All
scenarios in `../blueprint/features/*.feature` and all applicable entries
in `../blueprint/GUARANTEES.md` pass — see
`../blueprint/lineage/0003-rust-system-initial-generation.md` for the
initial generation record.
