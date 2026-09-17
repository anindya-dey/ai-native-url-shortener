# URL Shortener

This repository defines a URL shortener completely, before any code is
written. It contains what to build, what other systems can depend on, how
to verify correctness, and why past decisions were made. The spec/governance
artifacts live under `blueprint/`; the generated implementation lives at the
repository root.

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

## Status

An implementation exists at the repository root (`src/url_shortener/`,
`tests/`, `pyproject.toml`, `uv.lock`) — a FastAPI-based Python service
covering all three modules (URL creation, Redirect, Metadata). See
`blueprint/lineage/0001-system-initial-generation.md` for the record of this
generation: spec/acceptance versions used, the gap found and closed during
generation, and open follow-ups.
