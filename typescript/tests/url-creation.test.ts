import { describe, it, expect } from 'vitest';
import { makeApp, createUrl, isoInFuture, isoInPast, BASE_URL } from './support.js';

describe('Feature: URL creation', () => {
  it('Valid destination creates a short URL', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'https://example.com/a/long/path' });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(body.original_url).toBe('https://example.com/a/long/path');
    expect(body.code).toMatch(/^[A-Za-z0-9]{7}$/);
    expect(body.click_count).toBe(0);
    expect(body.expires_at).toBeNull();
  });

  it('Valid destination with a future expiration', async () => {
    const { app } = makeApp();
    const expiresAt = isoInFuture(60 * 60 * 1000);
    const res = await createUrl(app, { original_url: 'https://example.com', expires_at: expiresAt });
    expect(res.statusCode).toBe(201);
    const body = res.json();
    expect(new Date(body.expires_at).getTime()).toBe(new Date(expiresAt).getTime());
  });

  it('Unsupported scheme is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'ftp://example.com/file' });
    expect(res.statusCode).toBe(422);
  });

  it('Malformed URL is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'not a url' });
    expect(res.statusCode).toBe(422);
  });

  it('Oversized original_url is rejected', async () => {
    const { app } = makeApp();
    const oversized = `https://example.com/${'a'.repeat(2049)}`;
    const res = await createUrl(app, { original_url: oversized });
    expect(res.statusCode).toBe(422);
  });

  it('Scheme-only URL with no host is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'https://' });
    expect(res.statusCode).toBe(422);
  });

  it('URL with userinfo but no host is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'https://user@/path' });
    expect(res.statusCode).toBe(422);
  });

  it('original_url containing control characters is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'https://example.com/\r\nSet-Cookie: x=1' });
    expect(res.statusCode).toBe(422);
  });

  it('Missing original_url is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, {});
    expect(res.statusCode).toBe(422);
  });

  it('Past expiration is rejected', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, {
      original_url: 'https://example.com',
      expires_at: isoInPast(60 * 60 * 1000),
    });
    expect(res.statusCode).toBe(422);
  });

  it('short_url is built from the configured base URL and the code', async () => {
    const { app } = makeApp();
    const res = await createUrl(app, { original_url: 'https://example.com' });
    const body = res.json();
    expect(body.short_url).toMatch(/^https:\/\/short\.example\/[A-Za-z0-9]{7}$/);
    expect(body.short_url.endsWith(body.code)).toBe(true);
    expect(body.short_url).toBe(`${BASE_URL}/${body.code}`);
  });

  it('Submitting the same original_url twice creates two independent codes', async () => {
    const { app } = makeApp();
    const first = await createUrl(app, { original_url: 'https://example.com/same' });
    const second = await createUrl(app, { original_url: 'https://example.com/same' });
    expect(first.statusCode).toBe(201);
    expect(second.statusCode).toBe(201);
    expect(first.json().code).not.toBe(second.json().code);
  });

  // Gap closed in blueprint/specs/url-creation.md: "characters" for the
  // 2048 limit means Unicode code points, not UTF-16 code units — a
  // surrogate-pair character (one code point, two UTF-16 units in JS)
  // must count as one character.
  it('Length limit counts Unicode code points, not UTF-16 code units', async () => {
    const { app } = makeApp();
    const prefix = 'https://example.com/';
    const emoji = '\u{1F600}'; // one code point, two UTF-16 code units
    const filler = emoji.repeat(2048 - prefix.length);
    const exactly2048CodePoints = prefix + filler;
    expect([...exactly2048CodePoints].length).toBe(2048);
    expect(exactly2048CodePoints.length).toBeGreaterThan(2048);

    const res = await createUrl(app, { original_url: exactly2048CodePoints });
    expect(res.statusCode).toBe(201);

    const over = exactly2048CodePoints + emoji;
    const resOver = await createUrl(app, { original_url: over });
    expect(resOver.statusCode).toBe(422);
  });
});
