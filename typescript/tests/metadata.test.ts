import { describe, it, expect } from 'vitest';
import { ShortUrlSchema } from '../src/schemas.js';
import { makeApp, createUrl, isoInPast } from './support.js';

describe('Feature: Metadata', () => {
  it('Metadata for an active short URL', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com' });
    const code = created.json().code;
    await app.inject({ method: 'GET', url: `/${code}` });
    await app.inject({ method: 'GET', url: `/${code}` });
    await app.inject({ method: 'GET', url: `/${code}` });

    const res = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });

    expect(res.statusCode).toBe(200);
    expect(() => ShortUrlSchema.parse(res.json())).not.toThrow();
    expect(res.json().click_count).toBe(3);
  });

  it('Metadata for an expired short URL is still retrievable', async () => {
    const { app, store } = makeApp();
    const created = await createUrl(app, {
      original_url: 'https://example.com',
      expires_at: new Date(Date.now() + 60_000).toISOString(),
    });
    const code = created.json().code;
    // Force the record into the past without going through creation-time
    // validation, matching "Given an existing short URL ... that expired".
    const record = store.get(code);
    if (record) record.expiresAt = new Date(isoInPast(60 * 60 * 1000));

    const res = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });

    expect(res.statusCode).toBe(200);
    expect(new Date(res.json().expires_at).getTime()).toBeLessThan(Date.now());
  });

  it('Metadata for unknown code returns 404', async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: 'GET', url: '/api/v1/urls/zzzzzzz' });
    expect(res.statusCode).toBe(404);
    expect(res.json().detail).toBe('Short URL not found');
  });

  it('Metadata lookups never increment click_count', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com' });
    const code = created.json().code;

    for (let i = 0; i < 5; i += 1) {
      await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
    }

    const res = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
    expect(res.json().click_count).toBe(0);
  });

  it('Malformed code returns 404, not 422', async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: 'GET', url: '/api/v1/urls/ab' });
    expect(res.statusCode).toBe(404);
  });
});
