# 0002 — Redirect status is 302, not 301

**Status:** Accepted

## Context

`../specs/redirects.md` requires HTTP `302` for a successful redirect. `301`
(permanent redirect) was the obvious alternative and is what many
URL-shortener tutorials use.

## Decision

Use `302 Found` (temporary redirect) for every successful redirect,
unconditionally — never `301`.

## Alternatives considered

- **301 Permanent Redirect.** Rejected: browsers and intermediate caches are
  permitted to cache a `301` indefinitely and skip contacting the server on
  subsequent visits. That would make `click_count` undercount real usage
  after the first visit from a given client — directly violating the
  click-tracking guarantees in `../GUARANTEES.md`. It would also
  make it impossible to ever repoint a code to a different destination
  without stale caches serving the old one.
- **307 Temporary Redirect.** Considered equivalent for caching purposes to
  `302` but rejected for being unfamiliar to some HTTP clients/libraries
  that special-case `302` for legacy reasons; no behavioral requirement here
  needs `307`'s stricter method-preservation guarantee.

## Consequences

Every redirect request reaches the server, which is required for accurate
click counting but means the server is on the hot path for every single
redirect — no CDN/browser-cache shortcut is available by design. If click
counting requirements are ever relaxed, this decision should be revisited
alongside the guarantees it currently protects.
