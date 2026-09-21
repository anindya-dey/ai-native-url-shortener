# URL Shortener — Python implementation

One of several implementations of the specs in `../blueprint/`. See the
root `README.md` for how this fits alongside the others, and
`../AGENTS.md` for how to regenerate this implementation from scratch.

## Stack

FastAPI, Pydantic, an in-memory single-process thread-safe store. Test
suite: pytest + Hypothesis (property-based tests for
`../blueprint/GUARANTEES.md`).

## Running the service

**Prerequisites**: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

**Setup** (from this directory):

```
uv sync --group test
```

Installs both runtime and test dependencies.

**Required config**: `BASE_URL` must be set — an absolute `http`/`https`
URL with no trailing slash, used to build `short_url` values. There is no
default; the service fails fast at startup without it. This is deliberate
(see `../blueprint/specs/shared-conventions.md`), not a bug.

**Run the server**:

```
BASE_URL=https://short.example uv run uvicorn url_shortener.main:app --reload
```

**Run the tests**:

```
BASE_URL=https://short.example uv run --group test pytest tests -q
```

**Try it**:

```
curl -X POST "$BASE_URL/api/v1/urls" \
  -H 'content-type: application/json' \
  -d '{"original_url": "https://example.com/some/page"}'

curl "$BASE_URL/api/v1/urls/<code>"   # metadata
curl -i "$BASE_URL/<code>"            # redirect
```

See `../blueprint/contracts/openapi.yaml` for the full request/response
shapes.

## Status

All three modules (URL creation, Redirect, Metadata) are implemented. All
scenarios in `../blueprint/features/*.feature` and all applicable entries
in `../blueprint/GUARANTEES.md` pass — see
`../blueprint/lineage/0001-system-initial-generation.md` for the initial
generation record.

Three Medium-severity security-audit findings noted in that lineage entry
as open have since been resolved: the host-validation edge case is fixed
in `src/url_shortener/models.py`, a request body size cap is enforced in
`src/url_shortener/main.py`, and the Location-header percent-encoding
question is resolved by
`../blueprint/decisions/ADR-0007-location-header-preserves-percent-encoding.md`.
