# Specifications

These documents are the canonical behavior contract for the URL shortener.
They are written before implementation and remain the source of truth after
implementation exists. If code and spec disagree, the spec wins.

Acceptance criteria in each spec are written as Given-When-Then scenarios so
they map directly onto the scenarios in `../features/`. A spec change and
its corresponding scenario/guarantee change should land together.

- [Overview](overview.md) — scope, glossary, shared shape
- [Shared conventions](shared-conventions.md) — errors, time, naming
- [URL creation](url-creation.md) — validation and code generation
- [Redirects](redirects.md) — status codes, expiration checks, click tracking
- [Metadata](metadata.md) — non-redirecting lookup
- [Expiration](expiration.md) — expiry semantics and timezone handling

See `../contracts/openapi.yaml` for the machine-readable version of the wire
shape referenced throughout these specs, and `../MODULE_BOUNDARIES.md` for how
these specs map onto independently buildable modules.
