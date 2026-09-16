# Constitution

These principles are non-negotiable. An agent or engineer that cannot satisfy
one of these for a given change must stop and raise the conflict rather than
proceed silently.

## 1. Specs are canonical; code is a rendering

`specs/` describes what the system must do. Implementation code is generated
from it. If code and spec disagree, the spec wins — either the code is wrong,
or the spec is stale and must be updated *before* the code that contradicts
it is accepted.

## 2. Regenerate, don't patch

The default response to a bug or a changed requirement is to update the spec
and regenerate the affected module, not to edit the existing implementation
in place. In-place edits are a last resort, and are a signal — a signal that
either the spec was incomplete or the acceptance suite was insufficient to
catch the problem during regeneration. When an in-place edit is unavoidable,
the follow-up is not optional: fix the spec or acceptance gap that made the
patch necessary.

## 3. Nothing ships without acceptance criteria that survive the implementation

Every behavior described in `specs/` must have a corresponding scenario in
`acceptance/features/` or a guarantee in `acceptance/guarantees.md`. If a
requirement can't be checked mechanically and independently of the current
code, it isn't done — it's a claim.

## 4. Contracts change deliberately, never as a side effect

Files under `contracts/` define what other consumers depend on. Changing
them is always an explicit, flagged action with its own rationale — never an
incidental result of implementing an unrelated feature.

## 5. Every regeneration is recorded

After generating or regenerating any module, add an entry to
`regenerations/` recording which spec version and acceptance suite
version were used and what triggered the work. Undocumented regeneration is
indistinguishable from undocumented drift.

## 6. Modules are sized for deletion, not for convenience

Before adding a new module or expanding an existing one, apply the test
in `MODULE_BOUNDARIES.md`: can a human or agent understand it in about ten
minutes, verify it at its boundary without booting the rest of the system,
and delete it without dread? If not, the boundary is wrong before any code
is written.

## 7. The deletion test is a real, periodic exercise

Periodically — and always before declaring a module "done" — ask: if the
implementation were deleted right now, would `specs/` + `acceptance/` +
`contracts/` be sufficient to regenerate it with confidence? If the honest
answer relies on the current code, that gap gets written down and closed
before moving on.
