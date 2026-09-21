# URL Shortener

This is a spec-driven URL shortener with **multiple independent
implementations of the same behavior**. `blueprint/` is the immutable
oracle — specs, contracts, executable-scenario features, guarantees,
decisions, and lineage — governed by `blueprint/CONSTITUTION.md` and the
regeneration process in `AGENTS.md`. Every implementation lives in its own
top-level language directory, gets regenerated from `blueprint/`, and is
never edited around it (`blueprint/CONSTITUTION.md` §§1–2, 8).

The point isn't "here are three URL shorteners." It's that none of
`blueprint/` mentions a language, framework, or runtime — so the same
specs, the same contract, the same feature scenarios, and the same
guarantees produce a working implementation regardless of which one
generates it. See `blueprint/decisions/ADR-0008-multiple-parallel-language-implementations.md`
for why this repository is structured this way.

## What's here

| Directory/file | Answers |
|---|---|
| `blueprint/specs/` | What must the system do? |
| `blueprint/contracts/` | What must not break silently for anything depending on this service? |
| `blueprint/features/`, `blueprint/GUARANTEES.md` | How do we mechanically prove an implementation is correct? |
| `blueprint/decisions/`, `blueprint/lineage/` | Why does the system look the way it does, and what's been generated/regenerated, in which language, when? |
| `python/`, `typescript/`, `rust/` | Independent implementations of everything above. |

`blueprint/MODULE_BOUNDARIES.md` describes how each implementation should
be split into independently buildable, testable, and replaceable pieces —
the same boundaries apply regardless of language.

## Implementations

| Language | Framework | Status | Lineage |
|---|---|---|---|
| [`python/`](python/) | FastAPI | All modules implemented; all scenarios and guarantees pass | `blueprint/lineage/0001-system-initial-generation.md` |
| [`typescript/`](typescript/) | Fastify | All modules implemented; all scenarios and guarantees pass | `blueprint/lineage/0002-typescript-system-initial-generation.md` |
| [`rust/`](rust/) | Axum | All modules implemented; all scenarios and guarantees pass | `blueprint/lineage/0003-rust-system-initial-generation.md` |

Each language directory has its own README with setup and run
instructions specific to that implementation. Nothing about running or
testing one implementation depends on any other.

## Reading order

1. `blueprint/CONSTITUTION.md` — the rules that never get relaxed.
2. `AGENTS.md` — the operating procedure for generating or regenerating an
   implementation, in any language, from this repo.
3. `blueprint/specs/README.md` → each `blueprint/specs/*.md` — what to
   build.
4. `blueprint/contracts/openapi.yaml` — the wire-level shape that must not
   drift.
5. `blueprint/features/*.feature` + `blueprint/GUARANTEES.md` — what
   "correct" means (see `AGENTS.md`'s "Correctness artifacts" section for
   how to use these).
6. `blueprint/MODULE_BOUNDARIES.md` — how to decompose the work.
7. `blueprint/decisions/` — why past choices were made, before changing
   them.
8. Pick a language directory (`python/`, `typescript/`, `rust/`) for
   concrete, runnable code satisfying all of the above.

## Verifying implementations behave identically

Because `blueprint/contracts/openapi.yaml` and `blueprint/GUARANTEES.md`
don't reference any implementation, the same black-box test suite can run
against any of them over HTTP without modification. See
`contract-tests/README.md` once it exists for how to point that suite at
whichever language's server is currently running.
