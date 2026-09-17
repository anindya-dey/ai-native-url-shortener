# URL Shortener

This is a spec-driven Python URL shortener. `blueprint/` is the immutable
oracle — specs, contracts, executable-scenario features, guarantees,
decisions, and lineage — governed by `blueprint/CONSTITUTION.md` and the
regeneration process in `AGENTS.md`. The repository root holds the current
generated implementation (`src/`, `tests/`, `pyproject.toml`, `uv.lock`),
which must satisfy everything in `blueprint/` and gets regenerated from it,
not edited around it.

## What's here

| Directory/file | Answers |
|---|---|
| `blueprint/specs/` | What must the system do? |
| `blueprint/contracts/` | What must not break silently for anything depending on this service? |
| `blueprint/features/`, `blueprint/GUARANTEES.md` | How do we mechanically prove an implementation is correct? |
| `blueprint/decisions/`, `blueprint/lineage/` | Why does the system look the way it does, and what's been regenerated when? |

`blueprint/MODULE_BOUNDARIES.md` describes how the implementation should be
split into independently buildable, testable, and replaceable pieces.

## Reading order

1. `blueprint/CONSTITUTION.md` — the rules that never get relaxed.
2. `AGENTS.md` — the operating procedure for generating or regenerating code
   from this repo.
3. `blueprint/specs/README.md` → each `blueprint/specs/*.md` — what to build.
4. `blueprint/contracts/openapi.yaml` — the wire-level shape that must not
   drift.
5. `blueprint/features/*.feature` + `blueprint/GUARANTEES.md` — what
   "correct" means (see `AGENTS.md`'s "Correctness artifacts" section for
   how to use these).
6. `blueprint/MODULE_BOUNDARIES.md` — how to decompose the work.
7. `blueprint/decisions/` — why past choices were made, before changing
   them.

## Running the service

**Prerequisites**: Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

**Setup** (from the repo root):

```
uv sync --group test
```

Installs both runtime and test dependencies.

**Required config**: `BASE_URL` must be set — an absolute `http`/`https`
URL with no trailing slash, used to build `short_url` values. There is no
default; the service fails fast at startup without it. This is deliberate
(see `blueprint/specs/shared-conventions.md`), not a bug.

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

See `blueprint/contracts/openapi.yaml` for the full request/response shapes.

## Status

The implementation is in place at the repository root
(`src/url_shortener/`, `tests/`) — a FastAPI-based Python service covering
all three modules (URL creation, Redirect, Metadata). All scenarios in
`blueprint/features/*.feature` and all applicable entries in
`blueprint/GUARANTEES.md` pass.

`blueprint/lineage/0001-system-initial-generation.md` records the initial
generation and, at that point in time, left three Medium-severity
security-audit findings open. All three have since been resolved: the
host-validation edge case is fixed in `src/url_shortener/models.py`, a
request body size cap is enforced in `src/url_shortener/main.py`, and the
Location-header percent-encoding question is resolved by
`blueprint/decisions/ADR-0007-location-header-preserves-percent-encoding.md`.
The lineage entry itself is a point-in-time record and is left as written;
this section reflects current state.
