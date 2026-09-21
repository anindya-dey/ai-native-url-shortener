import { describe, it, expect } from 'vitest';
import { makeApp, createUrl } from './support.js';

describe('Feature: Redirects', () => {
  it('Redirect to an active short URL', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com/target' });
    const code = created.json().code;

    const res = await app.inject({ method: 'GET', url: `/${code}` });

    expect(res.statusCode).toBe(302);
    expect(res.headers.location).toBe('https://example.com/target');

    const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
    expect(metadata.json().click_count).toBe(1);
  });

  it('Unknown code returns 404', async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: 'GET', url: '/zzzzzzz' });
    expect(res.statusCode).toBe(404);
    expect(res.json().detail).toBe('Short URL not found');
  });

  it('Repeated redirects accumulate click_count', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com' });
    const code = created.json().code;

    for (let i = 0; i < 5; i += 1) {
      await app.inject({ method: 'GET', url: `/${code}` });
    }
    await app.inject({ method: 'GET', url: `/${code}` });

    const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
    expect(metadata.json().click_count).toBe(6);
  });

  it('Concurrent redirects do not lose click count', async () => {
    const { app } = makeApp();
    const created = await createUrl(app, { original_url: 'https://example.com' });
    const code = created.json().code;

    await Promise.all(
      Array.from({ length: 10 }, () => app.inject({ method: 'GET', url: `/${code}` })),
    );

    const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
    expect(metadata.json().click_count).toBe(10);
  });

  it('A 404 response does not modify click_count', async () => {
    const { app, store } = makeApp();
    await app.inject({ method: 'GET', url: '/zzzzzzz' });
    expect(store.get('zzzzzzz')).toBeUndefined();
  });

  it('Malformed code returns 404, not 422', async () => {
    const { app } = makeApp();
    const res = await app.inject({ method: 'GET', url: '/ab' });
    expect(res.statusCode).toBe(404);
    expect(res.json().detail).toBe('Short URL not found');
  });
});
