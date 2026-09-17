# Agent operating procedure

This file tells any coding agent (human-directed or autonomous) how to work
in this repository. Read `blueprint/CONSTITUTION.md` first — these are the
mechanics that implement those principles.

## Correctness artifacts: `blueprint/features/` and `blueprint/GUARANTEES.md`

Together these are the durable oracle for this system — what an agent uses
to decide whether a regenerated implementation is correct, independent of
how that implementation is built.

- `blueprint/features/*.feature` — Given-When-Then scenarios, one file per
  spec in `blueprint/specs/`. These are declarative. **They are not
  implemented yet** — there are no step definitions and no test runner
  wired up in this repository. When an agent generates the implementation,
  it also implements step definitions (or an equivalent executable test)
  for these scenarios in whatever language/framework the implementation
  uses. The `.feature` files themselves do not change based on
  implementation choice.
- `blueprint/GUARANTEES.md` — statements that must hold regardless of
  implementation, phrased so they could become property-based tests (e.g.
  via Hypothesis, fast-check, or similar) in any language.

What's deliberately not here: no implementation-specific test code (no
pytest files, no step-definition Python/JS, no fixtures). Those are
generated alongside the implementation, not committed to this spec-only
repository. Once an implementation exists, that generated test code is
disposable and can be regenerated at will, while `blueprint/features/*.feature`
and `blueprint/GUARANTEES.md` stay fixed as the target it has to keep
satisfying.

How to use these when implementing a feature:

1. Before implementing it, read its `.feature` file and any relevant
   entries in `blueprint/GUARANTEES.md`.
2. Implement step definitions/executable tests for every scenario.
3. Implement property-based tests for every applicable entry in
   `blueprint/GUARANTEES.md`.
4. Treat a module as regeneration-safe only once all of the above pass
   against the new implementation — not the old one.
5. If a scenario can't be satisfied as written, do not silently change the
   `.feature` file to match the implementation. Go back to the
   corresponding `blueprint/specs/*.md` file, resolve the discrepancy
   there, then update both the spec and the scenario together.

## Generating the implementation for the first time

1. Read every file in `blueprint/specs/`, `blueprint/contracts/`,
   `blueprint/features/`, and `blueprint/GUARANTEES.md` before writing any
   code. Do not start from an assumption about typical URL-shortener
   architecture — start from what's written here. Implementation code
   lives at the repository root (`src/`, `tests/`, `pyproject.toml`,
   `uv.lock`), never inside `blueprint/`. `blueprint/` holds `specs/`,
   `contracts/`, `features/`, `decisions/`, `lineage/`, `GUARANTEES.md`,
   `MODULE_BOUNDARIES.md`, and `CONSTITUTION.md` — implementation-agnostic
   and never modified by generated code itself, only by the processes
   described in this file.
2. Treat `blueprint/contracts/openapi.yaml` as fixed. The implementation
   must conform to it; it does not get to redefine it mid-generation.
3. For each `blueprint/specs/<feature>.md`, implement the behavior
   described, then confirm every scenario in
   `blueprint/features/<feature>.feature` and every applicable guarantee in
   `blueprint/GUARANTEES.md` passes.
4. Split the implementation to match `blueprint/MODULE_BOUNDARIES.md`. Do
   not merge modules that are listed there as independently buildable, and
   do not split a module finer than what's listed without updating that
   file to explain why.
5. Once the implementation passes every scenario in `blueprint/features/`
   and every applicable guarantee in `blueprint/GUARANTEES.md`, add a new
   entry to `blueprint/lineage/` (see `blueprint/lineage/README.md` for the
   required fields and naming convention), citing the actual commit or tag
   of `blueprint/specs/`/`blueprint/contracts/` used, and update
   `README.md`'s "Status" section to reflect that an implementation now
   exists — don't leave it claiming otherwise.

## Regenerating an existing module

1. Confirm which spec(s) govern the module from
   `blueprint/MODULE_BOUNDARIES.md`.
2. Re-read the current version of those specs — they may have changed since
   the implementation was last generated.
3. Delete the existing implementation for that module. Do not incrementally
   edit it. If deleting it causes dread rather than mild inconvenience, stop
   and fix the module boundary or the acceptance gap first (see
   `blueprint/CONSTITUTION.md` §6-7).
4. Regenerate from the current specs and contracts.
5. Run every scenario in that module's `blueprint/features/*.feature`
   file(s) and every applicable guarantee in `blueprint/GUARANTEES.md`, not
   just the ones you expect to be affected.
6. Add a new entry to `blueprint/lineage/`, following the naming convention
   and fields in `blueprint/lineage/README.md`, citing the actual commit or
   tag of `blueprint/specs/`/`blueprint/contracts/` used. Include the
   trigger (which spec changed, which incident, which new requirement) —
   this is what makes the history useful later.

## Handling gaps and ambiguity

If a spec is ambiguous or silent on a case the implementation needs to
handle:

1. Do not silently invent behavior and move on. Every gap you fill is a
   decision someone will need eventually.
2. Propose the resolution back into `blueprint/specs/<feature>.md` as an
   explicit rule or an explicit Given-When-Then scenario, and add the
   corresponding scenario to `blueprint/features/`.
3. Only then implement it. The spec update and the implementation should
   land together, not implementation first with the spec catching up later.

## Handling contract changes

If implementing a spec seems to require changing
`blueprint/contracts/openapi.yaml`:

1. Stop before changing the contract file.
2. State explicitly what would break for any other consumer of this
   contract and why the change is necessary.
3. Record the rationale as a decision under `blueprint/decisions/` before
   changing the contract, not after.

## What "done" means

A module is done when:

- Its behavior matches `blueprint/specs/`.
- Every scenario in the corresponding `blueprint/features/*.feature` file
  passes.
- Every applicable entry in `blueprint/GUARANTEES.md` holds.
- `blueprint/contracts/` is unchanged, or was changed with a recorded
  decision.
- `blueprint/lineage/` has a new entry for this work.

"All tests passed" is not sufficient on its own — confirm the acceptance
suite actually exercises what each spec requires, not just whatever the
implementation happens to do.
