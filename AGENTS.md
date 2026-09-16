# Agent operating procedure

This file tells any coding agent (human-directed or autonomous) how to work
in this repository. Read `CONSTITUTION.md` first — these are the mechanics
that implement those principles.

## Generating the implementation for the first time

1. Read every file in `specs/`, `contracts/`, and `acceptance/` before
   writing any code. Do not start from an assumption about typical
   URL-shortener architecture — start from what's written here.
   Implementation code lives alongside these directories (e.g. in `src/`
   or wherever suits the chosen language), never inside `specs/`,
   `contracts/`, `acceptance/`, `decisions/`, or `regenerations/` — those
   five directories are implementation-agnostic and are never modified by
   generated code itself, only by the processes described in this file.
2. Treat `contracts/openapi.yaml` as fixed. The implementation must conform
   to it; it does not get to redefine it mid-generation.
3. For each `specs/<feature>.md`, implement the behavior described, then
   confirm every scenario in `acceptance/features/<feature>.feature` and
   every applicable guarantee in `acceptance/guarantees.md` passes.
4. Split the implementation to match `MODULE_BOUNDARIES.md`. Do not merge
   modules that are listed there as independently buildable, and do not
   split a module finer than what's listed without updating that file
   to explain why.
5. Once the implementation passes every scenario and guarantee in
   `acceptance/`, add a new entry to `regenerations/` (see
   `regenerations/README.md` for the required fields and naming convention),
   citing the actual commit or tag of `specs/`/`contracts/` used, and
   update `README.md`'s "Status" section to reflect that an implementation
   now exists — don't leave it claiming otherwise.

## Regenerating an existing module

1. Confirm which spec(s) govern the module from `MODULE_BOUNDARIES.md`.
2. Re-read the current version of those specs — they may have changed since
   the implementation was last generated.
3. Delete the existing implementation for that module. Do not incrementally
   edit it. If deleting it causes dread rather than mild inconvenience, stop
   and fix the module boundary or the acceptance gap first (see
   `CONSTITUTION.md` §6-7).
4. Regenerate from the current specs and contracts.
5. Run the full acceptance suite for that module, not just the scenarios
   you expect to be affected.
6. Add a new entry to `regenerations/`, following the naming convention and
   fields in `regenerations/README.md`, citing the actual commit or tag of
   `specs/`/`contracts/` used. Include the trigger (which spec changed,
   which incident, which new requirement) — this is what makes the history
   useful later.

## Handling gaps and ambiguity

If a spec is ambiguous or silent on a case the implementation needs to
handle:

1. Do not silently invent behavior and move on. Every gap you fill is a
   decision someone will need eventually.
2. Propose the resolution back into `specs/<feature>.md` as an explicit rule
   or an explicit Given-When-Then scenario, and add the corresponding
   scenario to `acceptance/features/`.
3. Only then implement it. The spec update and the implementation should
   land together, not implementation first with the spec catching up later.

## Handling contract changes

If implementing a spec seems to require changing `contracts/openapi.yaml`:

1. Stop before changing the contract file.
2. State explicitly what would break for any other consumer of this
   contract and why the change is necessary.
3. Record the rationale as a decision under `decisions/` before changing the
   contract, not after.

## What "done" means

A module is done when:

- Its behavior matches `specs/`.
- Every scenario in the corresponding `acceptance/features/*.feature` file
  passes.
- Every applicable entry in `acceptance/guarantees.md` holds.
- `contracts/` is unchanged, or was changed with a recorded decision.
- `regenerations/` has a new entry for this work.

"All tests passed" is not sufficient on its own — confirm the acceptance
suite actually exercises what each spec requires, not just whatever the
implementation happens to do.
