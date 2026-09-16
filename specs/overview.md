# Overview

## Purpose

A service that accepts a long destination URL and returns a short code that
redirects to it. Optionally, a short URL can expire after a given time.

## Scope

In scope:
- Creating a short URL for an `http`/`https` destination.
- Redirecting a short code to its destination.
- Retrieving metadata for a short code without redirecting.
- Expiring short URLs after a configured time.
- Counting redirects (clicks) per short code.

Out of scope (not covered by any spec in this repository; do not implement):
- User accounts, authentication, or per-user ownership of short URLs.
- Custom/vanity short codes chosen by the caller.
- Analytics beyond a raw click count (no referrer tracking, no geo data).
- Rate limiting or abuse prevention.
- A user interface. This is an API-only system.

## Glossary

| Term | Meaning |
|---|---|
| Original URL | The destination the caller wants to shorten. Must be `http` or `https`. |
| Code | The generated identifier that stands in for the original URL. Seven characters, defined charset — see `url-creation.md`. |
| Short URL | The full redirectable URL formed from the service's base URL and the code. |
| Click | One successful redirect of a short URL to its original URL. |
| Expiration | The point after which a short URL stops redirecting successfully. |

## Shared API shape

Base path: `/api/v1`. Exact request/response shapes are defined in
`../contracts/openapi.yaml`. Field naming and cross-cutting conventions are
in `shared-conventions.md`.
