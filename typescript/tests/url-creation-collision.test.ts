import { describe, it, expect, vi, beforeEach } from 'vitest';

const real = await vi.importActual<typeof import('../src/codes.js')>('../src/codes.js');

let callCount = 0;
vi.mock('../src/codes.js', () => ({
  CODE_PATTERN: real.CODE_PATTERN,
  generateCode: () => {
    callCount += 1;
    return callCount === 1 ? 'abc1234' : real.generateCode();
  },
}));

beforeEach(() => {
  callCount = 0;
});

describe('Feature: URL creation', () => {
  it('Code collision is retried, not overwritten', async () => {
    const { makeApp, createUrl } = await import('./support.js');
    const { app, store } = makeApp();

    // First call to the stubbed generator returns "abc1234", seeding the
    // existing record the next request will collide with.
    const existing = await createUrl(app, { original_url: 'https://existing.example.com' });
    expect(existing.statusCode).toBe(201);
    expect(existing.json().code).toBe('abc1234');
    const existingSnapshot = { ...store.get('abc1234') };

    callCount = 0; // the next request's first attempt collides on "abc1234" again
    const res = await createUrl(app, { original_url: 'https://new.example.com' });

    expect(res.statusCode).toBe(201);
    expect(res.json().code).not.toBe('abc1234');
    expect(store.get('abc1234')).toEqual(existingSnapshot);
  });
});
