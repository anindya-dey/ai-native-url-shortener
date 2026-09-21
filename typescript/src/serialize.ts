import type { ShortUrlRecord } from './store.js';
import type { ShortUrl } from './schemas.js';

/**
 * short_url is always recomputed from `code` and the current BASE_URL, never
 * stored — see blueprint/decisions/ADR-0005-short-url-is-computed-not-stored.md.
 */
export function toShortUrl(record: ShortUrlRecord, baseUrl: string): ShortUrl {
  return {
    code: record.code,
    original_url: record.originalUrl,
    short_url: `${baseUrl}/${record.code}`,
    click_count: record.clickCount,
    created_at: record.createdAt.toISOString(),
    expires_at: record.expiresAt ? record.expiresAt.toISOString() : null,
  };
}
