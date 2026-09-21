import { CODE_PATTERN } from '../codes.js';
import type { Store } from '../store.js';
import type { ShortUrl } from '../schemas.js';
import { toShortUrl } from '../serialize.js';
import { NOT_FOUND_BODY } from '../errors.js';

export type MetadataResult =
  | { status: 200; body: ShortUrl }
  | { status: 404; body: typeof NOT_FOUND_BODY };

const NOT_FOUND: MetadataResult = { status: 404, body: NOT_FOUND_BODY };

/**
 * Metadata module — read-only lookup, expired or not. Performs no writes,
 * so it never touches click_count. See blueprint/MODULE_BOUNDARIES.md.
 */
export function getMetadata(store: Store, code: string, baseUrl: string): MetadataResult {
  if (!CODE_PATTERN.test(code)) {
    return NOT_FOUND;
  }
  const record = store.get(code);
  if (!record) {
    return NOT_FOUND;
  }
  return { status: 200, body: toShortUrl(record, baseUrl) };
}
