# URL Shortener — TypeScript implementation

One of several implementations of the specs in `../blueprint/`. See the
root `README.md` for how this fits alongside the others, and
`../AGENTS.md` for how to regenerate this implementation from scratch.

## Stack

Fastify, Zod (request-shape validation, mirroring the `ShortUrl` and
`ValidationError` schemas in `../blueprint/contracts/openapi.yaml`), an
in-memory single-process store. Test suite: Vitest + fast-check
(property-based tests for `../blueprint/GUARANTEES.md`).

## Running the service

**Prerequisites**: Node.js 20+ and npm.

**Setup** (from this directory):

```
npm install
```

Installs both runtime and test dependencies.

**Required config**: `BASE_URL` must be set — an absolute `http`/`https`
URL with no trailing slash, used to build `short_url` values. There is no
default; the service fails fast at startup without it. This is deliberate
(see `../blueprint/specs/shared-conventions.md`), not a bug.

**Run the server**:

```
BASE_URL=https://short.example npm start
```

**Run the tests**:

```
npm test
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
`../blueprint/lineage/0002-typescript-system-initial-generation.md` for
the initial generation record.
