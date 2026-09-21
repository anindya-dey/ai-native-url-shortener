export interface Config {
  baseUrl: string;
}

/**
 * BASE_URL is the one required piece of external configuration
 * (blueprint/specs/shared-conventions.md): absolute http(s) URL, no
 * trailing slash, no default — fail fast at startup if missing/invalid.
 */
export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const baseUrl = env.BASE_URL;
  if (!baseUrl) {
    throw new Error('BASE_URL environment variable is required');
  }
  if (baseUrl.endsWith('/')) {
    throw new Error('BASE_URL must not have a trailing slash');
  }
  let parsed: URL;
  try {
    parsed = new URL(baseUrl);
  } catch {
    throw new Error('BASE_URL must be an absolute http(s) URL');
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error('BASE_URL must use the http or https scheme');
  }
  return { baseUrl };
}
