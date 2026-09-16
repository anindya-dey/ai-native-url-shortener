# Regenerations

A record of every time an implementation was generated or regenerated from
this repository's specs. Each event gets its own file, following
`../decisions/`'s numbering convention — this keeps individual entries
small and lets an agent read only the entries relevant to the module
it's touching, instead of loading one ever-growing history file.

## Naming convention

`NNNN-module-short-description.md`, numbered sequentially across the
whole directory (not per module). Use the module name from
`../MODULE_BOUNDARIES.md`, or `system` for a full regeneration touching
every module at once.

Examples of filenames (not existing entries — illustrating the pattern
only): `0001-url-creation-initial-generation.md`,
`0002-redirect-fix-concurrency-gap.md`.

## Required fields in each entry

- **Date**
- **Module** — the module from `../MODULE_BOUNDARIES.md` this
  concerns, or `system` for a full regeneration
- **Spec version** — which spec file(s) governed this, and the actual
  commit or tag of them
- **Acceptance version** — which state of `../acceptance/features/`
  and `../acceptance/guarantees.md` was used to check the result
- **Trigger** — what caused this: initial generation, a changed spec, an
  incident, a dependency update
- **Agent/author** — who or what performed the regeneration
- **Result** — did every applicable scenario and guarantee pass; any gaps
  discovered, and whether they were closed by updating a spec, a contract,
  or `acceptance/`

Language, framework, and storage engine choices may be noted in **Result**
for context (they're useful history), but are never binding on future
regenerations. Nothing in this repository requires the next regeneration of
a module to reuse the same implementation choices as the last one — per
`../CONSTITUTION.md` §2, only behavior, contracts, and guarantees carry
forward; the "how" is free to change every time.

## Current state

No entries exist yet. This system has not been generated. Add the first
numbered file here the first time an agent generates an implementation from
the specs in this repository.
