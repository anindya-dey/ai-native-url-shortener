import Fastify from 'fastify';
import type { Config } from './config.js';
import { Store } from './store.js';
import { createShortUrl } from './modules/creation.js';
import { redirect } from './modules/redirect.js';
import { getMetadata } from './modules/metadata.js';

export function buildServer(config: Config, store: Store = new Store()) {
  const app = Fastify({ logger: false });

  app.post('/api/v1/urls', async (request, reply) => {
    const result = createShortUrl(request.body, { store, baseUrl: config.baseUrl });
    reply.code(result.status).send(result.body);
  });

  app.get('/api/v1/urls/:code', async (request, reply) => {
    const { code } = request.params as { code: string };
    const result = getMetadata(store, code, config.baseUrl);
    reply.code(result.status).send(result.body);
  });

  app.get('/:code', async (request, reply) => {
    const { code } = request.params as { code: string };
    const result = redirect(store, code, new Date());
    if (result.status === 302) {
      reply.code(302).header('Location', result.location).send();
    } else {
      reply.code(result.status).send(result.body);
    }
  });

  return app;
}
