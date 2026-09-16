# ADR-0001 — Record architecture decisions

**Status:** Accepted

## Context

Specs (`../specs/`) describe what the system must do. They don't naturally
carry *why* a particular rule was chosen over a plausible alternative. Without
a separate record, that reasoning either lives in someone's memory or gets
reconstructed after the fact when a future change appears to contradict a
rule with no visible justification.

## Decision

Every consequential design choice — one that a reasonable alternative
implementation might make differently — gets its own file under
`decisions/`, named `ADR-NNNN-short-title.md`, numbered sequentially,
following `ADR-TEMPLATE.md`. A decision is consequential if regenerating
this system from specs alone, without the decision record, could plausibly
produce a different (and equally spec-compliant) answer.

## Alternatives considered

- **Put rationale inline in `specs/*.md`.** Rejected: specs describe current
  required behavior; mixing in historical "why we didn't do X" makes specs
  longer and harder to keep current as decisions get revisited.
- **No formal record; rely on commit messages.** Rejected: commit messages
  are tied to a specific diff, not to a decision that may span multiple
  changes or get revisited long after the original commit.

## Consequences

Adds a small amount of process overhead per consequential decision. In
exchange, a future agent or engineer can distinguish "this behavior is
required" (spec) from "this behavior is required *because of this specific,
still-checkable reason*" (decision) — which is exactly what's needed before
safely changing something that looks arbitrary.
