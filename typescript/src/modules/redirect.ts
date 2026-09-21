import { CODE_PATTERN } from '../codes.js';
import type { Store } from '../store.js';
import { NOT_FOUND_BODY, EXPIRED_BODY } from '../errors.js';

export type RedirectResult =
  | { status: 302; location: string }
  | { status: 404; body: typeof NOT_FOUND_BODY }
  | { status: 410; body: typeof EXPIRED_BODY };

const NOT_FOUND: RedirectResult = { status: 404, body: NOT_FOUND_BODY };

/**
 * Redirect module — owns lookup, expiration check, and the
 * click_count increment. This function is synchronous end to end (no
 * `await` between reading and mutating the record), which is what makes
 * concurrent calls safe under Node's single-threaded event loop: each
 * call runs to completion before another can interleave.
 */
export function redirect(store: Store, code: string, now: Date): RedirectResult {
  if (!CODE_PATTERN.test(code)) {
    return NOT_FOUND;
  }
  const record = store.get(code);
  if (!record) {
    return NOT_FOUND;
  }
  if (record.expiresAt && record.expiresAt.getTime() <= now.getTime()) {
    return { status: 410, body: EXPIRED_BODY };
  }
  store.incrementClickCount(code);
  // encodeURI, not a full URL re-parse: percent-encodes characters unsafe
  // for HTTP header transport without otherwise restructuring the URL
  // (e.g. no trailing-slash addition) — see
  // blueprint/decisions/ADR-0007-location-header-preserves-percent-encoding.md.
  return { status: 302, location: encodeURI(record.originalUrl) };
}
