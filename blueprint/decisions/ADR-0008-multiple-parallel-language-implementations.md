# ADR-0008 — Support multiple parallel language implementations

**Status:** Accepted

## Context

Since initial generation (`lineage/0001`), this repository assumed exactly
one implementation lived at the repository root (`src/`, `tests/`,
`pyproject.toml`, `uv.lock`), and `AGENTS.md` said so explicitly. That
assumption was never load-bearing for `specs/`, `features/`,
`GUARANTEES.md`, or `contracts/` — none of them mention Python, FastAPI, or
any other implementation choice. It was, however, load-bearing for
`AGENTS.md`'s generation instructions and for the root `README.md`'s
"Status" section, both of which talked about "the implementation" as a
singular thing.

The premise of this project — specs are canonical, code is a disposable
rendering of them (`CONSTITUTION.md` §1) — implies the rendering language
shouldn't matter either. The only way to demonstrate that honestly, rather
than assert it, is to generate more than one implementation from the same
unmodified `blueprint/` and show they behave identically. That requires
more than one implementation directory existing at once, which the
single-root-directory assumption didn't allow for.

## Decision

The Python implementation moves from the repository root into `python/`
(`python/src/`, `python/tests/`, `python/pyproject.toml`,
`python/uv.lock`), preserved via `git mv` so file history carries over.
`typescript/` and `rust/` are added as sibling directories, each an
independent implementation of the same `blueprint/`. Any implementation
lives entirely inside its own top-level language directory; none lives
inside `blueprint/`, and none reaches into another language directory's
code. `CONSTITUTION.md` §8 makes this an explicit, permanent rule rather
than a one-off restructuring. `blueprint/lineage/` gains a required
**Language** field so history stays legible once more than one
implementation exists.

A shared, language-agnostic black-box test suite (outside any language
directory) is added separately to exercise `contracts/openapi.yaml` and
`GUARANTEES.md` over HTTP against whichever implementation is running,
without knowing or caring which language produced it. This is the
mechanism that actually proves parity, rather than three implementations
merely existing side by side unverified against each other.

## Alternatives considered

- **Keep one implementation at a time, swap languages by full
  regeneration.** This is what `CONSTITUTION.md` §2 and the original
  `lineage/README.md` already supported, and remains valid for a team that
  wants to migrate languages rather than run several at once. Rejected as
  the *only* mode: it can't demonstrate that the specs are actually
  language-independent, only that they were re-satisfied once, sequentially.
  Nothing here removes that option — a language directory can still be
  deleted and regenerated on its own, per `AGENTS.md`'s "Regenerating an
  existing module" process, without touching the others.
- **Put all implementations in one shared monorepo package structure
  (e.g. a single `src/` with language subfolders mixed with shared
  tooling).** Rejected: it would make each implementation's boundary
  fuzzier, not clearer, and complicates keeping each language's own
  package manager, lockfile, and test runner fully self-contained.
- **Treat only one implementation as canonical and the others as
  "reference ports" or examples.** Rejected: contradicts the actual
  thesis. If one implementation is privileged, the demonstration only
  proves that language matters less *most* of the time, not that the spec
  is genuinely the source of truth.

## Consequences

Adding a new language directory in the future (Go, Java, whatever) follows
the same pattern with no further `blueprint/` changes required beyond the
convention already established here. A behavior gap discovered while
implementing any one language must be closed in `specs/`/`features/`/
`GUARANTEES.md`, per `CONSTITUTION.md` §8 — not patched into only the
implementation that surfaced it — so every other language directory
benefits from the same fix. The cost is real: three implementations to
keep passing acceptance, three sets of tooling to maintain, and language-
specific edge cases (see, e.g., ADR-0007, found in the Python
implementation) that may need their own guarantee wording refinements as
each new language surfaces its own quirks.
