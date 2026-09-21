import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { Store } from '../src/store.js';
import { createShortUrl } from '../src/modules/creation.js';
import { getMetadata } from '../src/modules/metadata.js';
import { redirect } from '../src/modules/redirect.js';
import { CODE_PATTERN } from '../src/codes.js';
import { makeApp, createUrl, BASE_URL } from './support.js';

const lowercaseLetters = 'abcdefghijklmnopqrstuvwxyz'.split('');
const nonHttpSchemeArb = fc
  .array(fc.constantFrom(...lowercaseLetters), { minLength: 2, maxLength: 8 })
  .map((chars) => chars.join(''))
  .filter((s) => s !== 'http' && s !== 'https');

const baseUrlArb = fc
  .tuple(fc.constantFrom('http', 'https'), fc.domain())
  .map(([scheme, domain]) => `${scheme}://${domain}`);

// Property tests for every applicable entry in blueprint/GUARANTEES.md.
// Section headers below mirror that file's headers 1:1.

describe('Guarantees: Code generation', () => {
  it('Uniqueness while active + Shape: every created code is unique and matches the pattern', () => {
    fc.assert(
      fc.property(fc.integer({ min: 1, max: 40 }), (n) => {
        const store = new Store();
        const codes = new Set<string>();
        const shortUrls = new Set<string>();
        for (let i = 0; i < n; i += 1) {
          const result = createShortUrl({ original_url: 'https://example.com' }, { store, baseUrl: BASE_URL });
          expect(result.status).toBe(201);
          if (result.status === 201) {
            expect(result.body.code).toMatch(CODE_PATTERN);
            codes.add(result.body.code);
            shortUrls.add(result.body.short_url);
          }
        }
        expect(codes.size).toBe(n);
        // short_url construction, "no two records share a short_url while
        // active" — a direct consequence of code uniqueness (see
        // GUARANTEES.md's "short_url construction" section).
        expect(shortUrls.size).toBe(n);
      }),
      { numRuns: 20 },
    );
  });

  it('No overwrite on collision: a rejected insert never changes the existing record', () => {
    const codePool = ['aaaaaaa', 'bbbbbbb', 'ccccccc', 'ddddddd', 'eeeeeee'];
    fc.assert(
      fc.property(fc.array(fc.constantFrom(...codePool), { minLength: 1, maxLength: 30 }), (codes) => {
        const store = new Store();
        const firstMarkerForCode = new Map<string, string>();
        codes.forEach((code, index) => {
          const marker = `marker-${index}`;
          const inserted = store.tryInsert({
            code,
            originalUrl: marker,
            clickCount: 0,
            createdAt: new Date(),
            expiresAt: null,
          });
          if (inserted) firstMarkerForCode.set(code, marker);
        });
        for (const code of new Set(codes)) {
          expect(store.get(code)?.originalUrl).toBe(firstMarkerForCode.get(code));
        }
      }),
    );
  });
});

describe('Guarantees: Click tracking', () => {
  it('click_count is monotonic non-negative across any sequence of redirect/metadata calls', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.constantFrom('redirect', 'metadata'), { minLength: 0, maxLength: 15 }),
        async (ops) => {
          const { app } = makeApp();
          const created = await createUrl(app, { original_url: 'https://example.com' });
          const code = created.json().code;
          let previous = 0;
          for (const op of ops) {
            const path = op === 'redirect' ? `/${code}` : `/api/v1/urls/${code}`;
            await app.inject({ method: 'GET', url: path });
            const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
            const current = metadata.json().click_count;
            expect(current).toBeGreaterThanOrEqual(previous);
            expect(current).toBeGreaterThanOrEqual(0);
            previous = current;
          }
        },
      ),
      { numRuns: 10 },
    );
  });

  it('Exactly-once per successful redirect: N concurrent redirects increase click_count by exactly N', async () => {
    await fc.assert(
      fc.asyncProperty(fc.integer({ min: 1, max: 25 }), async (n) => {
        const { app } = makeApp();
        const created = await createUrl(app, { original_url: 'https://example.com' });
        const code = created.json().code;

        await Promise.all(
          Array.from({ length: n }, () => app.inject({ method: 'GET', url: `/${code}` })),
        );

        const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
        expect(metadata.json().click_count).toBe(n);
      }),
      { numRuns: 15 },
    );
  });

  it('No increment on failure: unknown/malformed codes never change click_count', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 12 }).filter((s) => !CODE_PATTERN.test(s)),
        async (badCode) => {
          const { app, store } = makeApp();
          const created = await createUrl(app, { original_url: 'https://example.com' });
          const goodCode = created.json().code;

          await app.inject({ method: 'GET', url: `/${encodeURIComponent(badCode)}` });

          expect(store.get(goodCode)?.clickCount).toBe(0);
        },
      ),
      { numRuns: 20 },
    );
  });

  it('No increment on failure: redirecting an expired code (410) never changes click_count', async () => {
    await fc.assert(
      fc.asyncProperty(fc.integer({ min: 0, max: 10_000_000 }), async (msInPast) => {
        const { app, store } = makeApp();
        const created = await createUrl(app, {
          original_url: 'https://example.com',
          expires_at: new Date(Date.now() + 60_000).toISOString(),
        });
        const code = created.json().code;
        const record = store.get(code);
        if (record) record.expiresAt = new Date(Date.now() - msInPast);

        const res = await app.inject({ method: 'GET', url: `/${code}` });

        expect(res.statusCode).toBe(410);
        expect(store.get(code)?.clickCount).toBe(0);
      }),
      { numRuns: 20 },
    );
  });

  it('No increment on metadata read, for any number of reads', async () => {
    await fc.assert(
      fc.asyncProperty(fc.integer({ min: 0, max: 20 }), async (n) => {
        const { app } = makeApp();
        const created = await createUrl(app, { original_url: 'https://example.com' });
        const code = created.json().code;

        for (let i = 0; i < n; i += 1) {
          await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
        }

        const metadata = await app.inject({ method: 'GET', url: `/api/v1/urls/${code}` });
        expect(metadata.json().click_count).toBe(0);
      }),
      { numRuns: 15 },
    );
  });
});

describe('Guarantees: short_url construction', () => {
  it('short_url is deterministic from code and the *current* BASE_URL, not a stored literal', () => {
    fc.assert(
      fc.property(baseUrlArb, baseUrlArb, (baseA, baseB) => {
        const store = new Store();
        const created = createShortUrl({ original_url: 'https://example.com' }, { store, baseUrl: baseA });
        expect(created.status).toBe(201);
        if (created.status !== 201) return;
        const code = created.body.code;

        const viaA = getMetadata(store, code, baseA);
        const viaB = getMetadata(store, code, baseB); // simulates BASE_URL changing between reads
        expect(viaA.status).toBe(200);
        expect(viaB.status).toBe(200);
        if (viaA.status === 200) expect(viaA.body.short_url).toBe(`${baseA}/${code}`);
        if (viaB.status === 200) expect(viaB.body.short_url).toBe(`${baseB}/${code}`);
      }),
    );
  });
});

describe('Guarantees: Duplicate submissions', () => {
  it('No implicit deduplication: N submissions of the same original_url produce N distinct codes', () => {
    fc.assert(
      fc.property(fc.webUrl(), fc.integer({ min: 1, max: 20 }), (url, n) => {
        const store = new Store();
        const codes = new Set<string>();
        for (let i = 0; i < n; i += 1) {
          const result = createShortUrl({ original_url: url }, { store, baseUrl: BASE_URL });
          expect(result.status).toBe(201);
          if (result.status === 201) codes.add(result.body.code);
        }
        expect(codes.size).toBe(n);
      }),
      { numRuns: 20 },
    );
  });
});

describe('Guarantees: Round-trip integrity', () => {
  it('original_url is preserved exactly through metadata for any valid URL', () => {
    fc.assert(
      fc.property(fc.webUrl(), (url) => {
        const store = new Store();
        const created = createShortUrl({ original_url: url }, { store, baseUrl: BASE_URL });
        expect(created.status).toBe(201);
        if (created.status !== 201) return;
        const meta = getMetadata(store, created.body.code, BASE_URL);
        expect(meta.status).toBe(200);
        if (meta.status === 200) expect(meta.body.original_url).toBe(url);
      }),
    );
  });

  it('redirect Location header is percent-encoding-equivalent to original_url (ADR-0007)', () => {
    fc.assert(
      fc.property(fc.webUrl(), (url) => {
        const store = new Store();
        const created = createShortUrl({ original_url: url }, { store, baseUrl: BASE_URL });
        expect(created.status).toBe(201);
        if (created.status !== 201) return;
        const result = redirect(store, created.body.code, new Date());
        expect(result.status).toBe(302);
        if (result.status === 302) expect(decodeURI(result.location)).toBe(url);
      }),
    );
  });

  it('expires_at round-trips as the same UTC instant, whether submitted naive or with an explicit offset', () => {
    fc.assert(
      fc.property(fc.integer({ min: 1000, max: 365 * 24 * 60 * 60 * 1000 }), fc.boolean(), (msFromNow, naive) => {
        const store = new Store();
        const future = new Date(Date.now() + msFromNow);
        const iso = future.toISOString();
        const submitted = naive ? iso.replace('Z', '') : iso;
        const created = createShortUrl(
          { original_url: 'https://example.com', expires_at: submitted },
          { store, baseUrl: BASE_URL },
        );
        expect(created.status).toBe(201);
        if (created.status === 201) {
          expect(new Date(created.body.expires_at as string).getTime()).toBe(future.getTime());
        }
      }),
      { numRuns: 30 },
    );
  });
});

describe('Guarantees: Expiration', () => {
  it('Boundary is inclusive: expires_at at or before "now" is treated as expired', () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 100_000 }), (msAtOrBeforeNow) => {
        const store = new Store();
        const now = new Date();
        store.tryInsert({
          code: 'aaaaaaa',
          originalUrl: 'https://example.com',
          clickCount: 0,
          createdAt: now,
          expiresAt: new Date(now.getTime() - msAtOrBeforeNow),
        });
        expect(redirect(store, 'aaaaaaa', now).status).toBe(410);
      }),
    );
  });

  it("Expiration doesn't affect metadata visibility, regardless of expires_at", () => {
    fc.assert(
      fc.property(fc.option(fc.integer({ min: -1_000_000, max: 1_000_000 }), { nil: null }), (offsetMs) => {
        const store = new Store();
        const now = new Date();
        store.tryInsert({
          code: 'bbbbbbb',
          originalUrl: 'https://example.com',
          clickCount: 0,
          createdAt: now,
          expiresAt: offsetMs === null ? null : new Date(now.getTime() + offsetMs),
        });
        expect(getMetadata(store, 'bbbbbbb', BASE_URL).status).toBe(200);
      }),
    );
  });

  it('Absence of expires_at means permanence: redirects at any future time, arbitrarily far out', () => {
    fc.assert(
      fc.property(fc.integer({ min: 0, max: 100 * 365 * 24 * 60 * 60 * 1000 }), (msInFuture) => {
        const store = new Store();
        const now = new Date();
        store.tryInsert({
          code: 'ccccccc',
          originalUrl: 'https://example.com',
          clickCount: 0,
          createdAt: now,
          expiresAt: null,
        });
        const farFuture = new Date(now.getTime() + msInFuture);
        expect(redirect(store, 'ccccccc', farFuture).status).toBe(302);
      }),
    );
  });
});

describe('Guarantees: Validation', () => {
  it('Scheme restriction is exhaustive: any scheme other than http/https is rejected', () => {
    fc.assert(
      fc.property(nonHttpSchemeArb, (scheme) => {
        const store = new Store();
        const result = createShortUrl(
          { original_url: `${scheme}://example.com/file` },
          { store, baseUrl: BASE_URL },
        );
        expect(result.status).toBe(422);
      }),
    );
  });

  it('Length restriction is exhaustive: any length beyond 2048 code points is rejected', () => {
    fc.assert(
      fc.property(fc.integer({ min: 1, max: 5000 }), (extra) => {
        const store = new Store();
        const prefix = 'https://example.com/';
        const url = prefix + 'a'.repeat(2048 - prefix.length + extra);
        const result = createShortUrl({ original_url: url }, { store, baseUrl: BASE_URL });
        expect(result.status).toBe(422);
      }),
      { numRuns: 20 },
    );
  });

  it('Malformed and missing codes are indistinguishable to the caller, on both endpoints', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 12 }).filter((s) => !CODE_PATTERN.test(s)),
        async (malformed) => {
          const { app } = makeApp();
          const encoded = encodeURIComponent(malformed);

          const wellFormedMissing = await app.inject({ method: 'GET', url: '/zzzzzzz' });
          const malformedRedirect = await app.inject({ method: 'GET', url: `/${encoded}` });
          expect(malformedRedirect.statusCode).toBe(wellFormedMissing.statusCode);
          expect(malformedRedirect.json()).toEqual(wellFormedMissing.json());

          const wellFormedMissingMeta = await app.inject({ method: 'GET', url: '/api/v1/urls/zzzzzzz' });
          const malformedMeta = await app.inject({ method: 'GET', url: `/api/v1/urls/${encoded}` });
          expect(malformedMeta.statusCode).toBe(wellFormedMissingMeta.statusCode);
          expect(malformedMeta.json()).toEqual(wellFormedMissingMeta.json());
        },
      ),
      { numRuns: 30 },
    );
  });
});
