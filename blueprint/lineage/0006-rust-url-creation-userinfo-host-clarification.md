# 0006 — rust: URL creation userinfo-host clarification

- **Date**: 2026-09-23
- **Language**: `rust`
- **Module**: URL creation
- **Spec version**: `blueprint/specs/url-creation.md` in the working tree after
  `881de67` ("Add shared black-box contract/guarantee test suite"), with this
  clarification uncommitted; no commit containing the edit is claimed.
- **Acceptance version**: `blueprint/features/url-creation.feature` in the
  same working tree, with this uncommitted scenario; `GUARANTEES.md` unchanged:
  ```gherkin
  Scenario: URL with userinfo but no host is rejected
    Given no prior state
    When the client POSTs to /api/v1/urls with original_url "https://user@/path"
    Then the response status is 422
  ```
- **Trigger**: Acceptance/spec clarification and executable test coverage
  update, not a regenerated implementation. Added the rule: “A URL with
  userinfo but an empty host (e.g. `https://user@/path` or
  `https://user:pass@/path`) is rejected as lacking a non-empty host.”
- **Agent/author**: Docs Writer + Tester, coordinated by Cortana
- **Result**: The implementation-specific scenario test is already recorded in
  `rust/tests/url_creation.rs`; shared black-box coverage was added at
  `contract-tests/test_url_creation.py`. The shared black-box contract suite
  passed 48 tests against each of Python, TypeScript, and Rust. The existing
  implementation already rejected the clarified input, so no
  implementation code changed. `git diff --check` was clean.
