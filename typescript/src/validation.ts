// C0 controls (\x00-\x1F), DEL (\x7F), and C1 controls (\x80-\x9F).
const CONTROL_CHAR_RE = /[\u0000-\u001F\u007F-\u009F]/;
const SCHEME_RE = /^https?:\/\//;
const MAX_ORIGINAL_URL_LENGTH = 2048;

/**
 * Length is counted in Unicode code points (spreading a string iterates
 * code points, correctly counting a surrogate pair as one character) —
 * see blueprint/specs/url-creation.md's note on this, added because
 * JavaScript's native `string.length` counts UTF-16 code units instead,
 * which would double-count astral-plane characters (e.g. many emoji)
 * relative to Python's `len()`.
 */
function codePointLength(value: string): number {
  return [...value].length;
}

/** Returns an error message, or null if `value` is an acceptable original_url. */
export function validateOriginalUrl(value: string): string | null {
  if (CONTROL_CHAR_RE.test(value)) {
    return 'original_url must not contain control characters';
  }
  if (codePointLength(value) > MAX_ORIGINAL_URL_LENGTH) {
    return `original_url must not exceed ${MAX_ORIGINAL_URL_LENGTH} characters`;
  }
  if (!SCHEME_RE.test(value)) {
    return 'original_url must use the http or https scheme';
  }
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    return 'original_url must be a valid URL';
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return 'original_url must use the http or https scheme';
  }
  if (!parsed.hostname) {
    return 'original_url must include a host';
  }
  return null;
}

type ExpiresAtParseResult = { date: Date } | { error: string };

const HAS_TIMEZONE_RE = /(?:Z|[+-]\d{2}:?\d{2})$/i;

/**
 * A naive (timezone-less) expires_at is interpreted as UTC per
 * blueprint/specs/shared-conventions.md. This must be done explicitly:
 * unlike Python, JavaScript's `Date` parses a timezone-less date-time
 * string as local time, not UTC, per the ECMA-262 Date Time String Format.
 */
export function parseExpiresAt(raw: string): ExpiresAtParseResult {
  const trimmed = raw.trim();
  const normalized = HAS_TIMEZONE_RE.test(trimmed) ? trimmed : `${trimmed}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return { error: 'expires_at must be a valid ISO 8601 timestamp' };
  }
  return { date };
}
