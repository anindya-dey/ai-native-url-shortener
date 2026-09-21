# Lineage

A record of every time an implementation was generated or regenerated from
this repository's specs. Each event gets its own file, following
`../decisions/`'s numbering convention — this keeps individual entries
small and lets an agent read only the entries relevant to the module
it's touching, instead of loading one ever-growing history file.

## Naming convention

`NNNN-language-module-short-description.md`, numbered sequentially across
the whole directory (not per module, not per language). Use the language
directory name (`python`, `typescript`, `rust`, ...) and the module name
from `../MODULE_BOUNDARIES.md`, or `system` for a full regeneration
touching every module at once.

Examples of filenames (not existing entries — illustrating the pattern
only): `0002-typescript-url-creation-initial-generation.md`,
`0003-python-redirect-fix-concurrency-gap.md`.

`0001` predates this convention and keeps its original name
(`0001-system-initial-generation.md`) — it's identified as Python via its
required **Language** field below instead of its filename. Don't rename
it retroactively.

## Required fields in each entry

- **Date**
- **Language** — which language directory this concerns (`python`,
  `typescript`, `rust`, ...). Each language directory's lineage is
  independent: an entry for `typescript` says nothing about whether
  `python`'s implementation of the same module is current.
- **Module** — the module from `../MODULE_BOUNDARIES.md` this
  concerns, or `system` for a full regeneration
- **Spec version** — which spec file(s) governed this, and the actual
  commit or tag of them
- **Acceptance version** — which state of `../features/`
  and `../GUARANTEES.md` was used to check the result
- **Trigger** — what caused this: initial generation, a changed spec, an
  incident, a dependency update
- **Agent/author** — who or what performed the regeneration
- **Result** — did every applicable scenario and guarantee pass; any gaps
  discovered, and whether they were closed by updating a spec, a contract,
  a feature file, or `GUARANTEES.md`

Framework and storage engine choices within the chosen language may be
noted in **Result** for context (they're useful history), but are never
binding on future regenerations. Nothing in this repository requires the
next regeneration of a module — in that language or a new one — to reuse
the same implementation choices as the last one. Per `../CONSTITUTION.md`
§2 and §8, only behavior, contracts, and guarantees carry forward; the
"how," including the language itself, is free to change every time.

## Current state

`python/` has one lineage entry (`0001`, full initial generation).
`typescript/` has one lineage entry (`0002`, full initial generation).
`rust/` does not exist yet. Add a new numbered file here the first time an
agent generates an implementation in a new language directory, or
regenerates a module in an existing one.
