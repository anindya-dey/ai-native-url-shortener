# Acceptance

This directory holds the durable oracle for this system — the artifacts an
agent uses to decide whether a regenerated implementation is correct,
independent of how that implementation is built.

## What's here

- `features/*.feature` — Given-When-Then scenarios, one file per spec in
  `../specs/`. These are declarative. **They are not implemented yet** —
  there are no step definitions and no test runner wired up in this
  repository. When an agent generates the implementation, it also
  implements step definitions (or an equivalent executable test) for these
  scenarios in whatever language/framework the implementation uses. The
  `.feature` files themselves do not change based on implementation choice.
- `guarantees.md` — statements that must hold regardless of implementation,
  phrased so they could become property-based tests (e.g. via Hypothesis,
  fast-check, or similar) in any language.

## What's deliberately not here

No implementation-specific test code (no pytest files, no step-definition
Python/JS, no fixtures). Those are generated alongside the implementation,
not committed to this spec-only repository. Once an implementation exists,
that generated test code is disposable and can be regenerated at will,
while these `.feature` files and `guarantees.md` stay fixed as the target
it has to keep satisfying.

## How an agent should use this directory

1. Before implementing a feature, read its `.feature` file and any relevant
   entries in `guarantees.md`.
2. Implement step definitions/executable tests for every scenario.
3. Implement property-based tests for every applicable entry in
   `guarantees.md`.
4. Treat a module as regeneration-safe only once all of the above pass
   against the new implementation — not the old one.
5. If a scenario can't be satisfied as written, do not silently change the
   `.feature` file to match the implementation. Go back to the corresponding
   `../specs/*.md` file, resolve the discrepancy there, then update both the
   spec and the scenario together.
