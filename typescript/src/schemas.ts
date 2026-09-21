import { z } from 'zod';

// Mirrors CreateUrlRequest in blueprint/contracts/openapi.yaml, including
// additionalProperties: false.
export const CreateUrlRequestSchema = z
  .object({
    original_url: z.string(),
    expires_at: z.string().optional(),
  })
  .strict();

// Mirrors the ShortUrl schema in blueprint/contracts/openapi.yaml.
export const ShortUrlSchema = z.object({
  code: z.string().regex(/^[A-Za-z0-9]{7}$/),
  original_url: z.string(),
  short_url: z.string(),
  click_count: z.number().int().min(0),
  created_at: z.string(),
  expires_at: z.string().nullable(),
});

export const ValidationErrorSchema = z.object({ detail: z.string() });
export const NotFoundErrorSchema = z.object({ detail: z.literal('Short URL not found') });
export const ExpiredErrorSchema = z.object({ detail: z.literal('Short URL has expired') });

export type ShortUrl = z.infer<typeof ShortUrlSchema>;
