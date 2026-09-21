import type { FastifyInstance } from 'fastify';
import { buildServer } from '../src/server.js';
import { Store } from '../src/store.js';

export const BASE_URL = 'https://short.example';

export function makeApp(): { app: FastifyInstance; store: Store } {
  const store = new Store();
  const app = buildServer({ baseUrl: BASE_URL }, store);
  return { app, store };
}

export async function createUrl(
  app: FastifyInstance,
  body: Record<string, unknown>,
) {
  return app.inject({ method: 'POST', url: '/api/v1/urls', payload: body });
}

export function isoInFuture(ms: number): string {
  return new Date(Date.now() + ms).toISOString();
}

export function isoInPast(ms: number): string {
  return new Date(Date.now() - ms).toISOString();
}
