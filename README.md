# URL Shortener

This repository defines a URL shortener completely, before any code is
written. It contains what to build, what other systems can depend on, how
to verify correctness, and why past decisions were made. No implementation
exists yet — that gets generated from these files.

## What's here

| Directory | Answers |
|---|---|
| `specs/` | What must the system do? |
| `contracts/` | What must not break silently for anything depending on this service? |
| `acceptance/` | How do we mechanically prove an implementation is correct? |
| `decisions/`, `regenerations/` | Why does the system look the way it does, and what's been regenerated when? |

`MODULE_BOUNDARIES.md` describes how the implementation should be split into
independently buildable, testable, and replaceable pieces.

## Reading order

1. `CONSTITUTION.md` — the rules that never get relaxed.
2. `AGENTS.md` — the operating procedure for generating or regenerating code
   from this repo.
3. `specs/README.md` → each `specs/*.md` — what to build.
4. `contracts/openapi.yaml` — the wire-level shape that must not drift.
5. `acceptance/README.md` → `acceptance/features/*.feature` +
   `acceptance/guarantees.md` — what "correct" means.
6. `MODULE_BOUNDARIES.md` — how to decompose the work.
7. `decisions/` — why past choices were made, before changing them.

## Status

No implementation exists yet. `regenerations/` has no entries. The first one
will be written the first time an agent generates an implementation from
these specs.
