import type { z } from 'zod';
import { CreateUrlRequestSchema } from '../schemas.js';
import type { ShortUrl } from '../schemas.js';
import { generateCode } from '../codes.js';
import type { Store, ShortUrlRecord } from '../store.js';
import { toShortUrl } from '../serialize.js';
import { validateOriginalUrl, parseExpiresAt } from '../validation.js';

export type CreateResult =
  | { status: 201; body: ShortUrl }
  | { status: 422; body: { detail: string } };

export interface CreateDeps {
  store: Store;
  baseUrl: string;
  now?: Date;
}

function describeBodyError(error: z.ZodError): string {
  const missingOriginalUrl = error.issues.some(
    (issue) => issue.path[0] === 'original_url' && issue.code === 'invalid_type',
  );
  if (missingOriginalUrl) {
    return 'original_url is required';
  }
  const unrecognized = error.issues.find((issue) => issue.code === 'unrecognized_keys');
  if (unrecognized && 'keys' in unrecognized) {
    return `Unexpected field(s): ${unrecognized.keys.join(', ')}`;
  }
  return 'Invalid request body';
}

/**
 * URL creation module — owns generating and persisting new records
 * (including collision retry) and the creation-time slice of the
 * expiration rule. See blueprint/MODULE_BOUNDARIES.md.
 */
export function createShortUrl(input: unknown, deps: CreateDeps): CreateResult {
  const now = deps.now ?? new Date();

  const parsedBody = CreateUrlRequestSchema.safeParse(input);
  if (!parsedBody.success) {
    return { status: 422, body: { detail: describeBodyError(parsedBody.error) } };
  }
  const { original_url, expires_at } = parsedBody.data;

  const urlError = validateOriginalUrl(original_url);
  if (urlError) {
    return { status: 422, body: { detail: urlError } };
  }

  let expiresAt: Date | null = null;
  if (expires_at !== undefined) {
    const parsed = parseExpiresAt(expires_at);
    if ('error' in parsed) {
      return { status: 422, body: { detail: parsed.error } };
    }
    if (parsed.date.getTime() <= now.getTime()) {
      return { status: 422, body: { detail: 'expires_at must be strictly in the future' } };
    }
    expiresAt = parsed.date;
  }

  const record: ShortUrlRecord = {
    code: generateCode(),
    originalUrl: original_url,
    clickCount: 0,
    createdAt: now,
    expiresAt,
  };
  while (!deps.store.tryInsert(record)) {
    record.code = generateCode();
  }

  return { status: 201, body: toShortUrl(record, deps.baseUrl) };
}
