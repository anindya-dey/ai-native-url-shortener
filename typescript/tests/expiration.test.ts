import { describe, it, expect } from 'vitest';
import { makeApp, createUrl, isoInPast, isoInFuture } from './support.js';

describe('Feature: Expiration', () => {
  it('Redirect to an expired short URL returns 410', async () => {
    const { app, store } = makeApp();
    const created = await createUrl(app, {
      original_url: 'https://example.com',
      expires_at: isoInFuture(60_000),
    });
    const code = created.json().code;
    const record = store.get(code);
    if (record) record.expiresAt = new Date(isoInPast(60 * 60 * 1000));

    const res = await app.inject({ method: 'GET', url: `/${code}` });

    expect(res.statusCode).toBe(410);
    expect(res.json().detail).toBe('Short URL has expired');
    expect(store.get(code)?.clickCount).toBe(0);
  });

  it('Redirect at the exact expiration boundary is treated as expired', async () => {
    const { app, store } = makeApp();
    const created = await createUrl(app, {
      original_url: 'https://example.com',
      expires_at: isoInFuture(60_000),
    });
    const code = created.json().code;
    const now = new Date();
    const record = store.get(code);
    if (record) record.expiresAt = now;

    // The route handler stamps "now" itself; a boundary of "now" as seen by
    // the handler is guaranteed by expiresAt <= now, which holds for any
    // instant at or after the moment we just set above.
    const res = await app.inject({ method: 'GET', url: `/${code}` });

    expect(res.statusCode).toBe(410);
  });

  it('A short URL with no expires_at never expires', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com' });
    const code = created.json().code;

    const res = await app.inject({ method: 'GET', url: `/${code}` });

    expect(res.statusCode).toBe(302);
  });

  it('A naive expires_at at creation is interpreted as UTC', async () => {
    const { app } = makeApp();
    const future = new Date(Date.now() + 60 * 60 * 1000);
    const naive = future.toISOString().replace('Z', ''); // strip timezone designator

    const res = await createUrl(app, { original_url: 'https://example.com', expires_at: naive });

    expect(res.statusCode).toBe(201);
    expect(new Date(res.json().expires_at).getTime()).toBe(future.getTime());
  });

  it('Metadata remains available after expiration', async () => {
    const { app, store } = makeApp();
    const created = await createUrl(app, {
      original_url: 'https://example.com',
      expires_at: isoInFuture(60_000),
    });
    const code = created.json().code;
    const record = store.get(code);
    if (record) record.expiresAt = new Date(isoInPast(60 * 60 * 1000));

    const res = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });

    expect(res.statusCode).toBe(200);
    expect(new Date(res.json().expires_at).getTime()).toBeLessThan(Date.now());
  });
});
