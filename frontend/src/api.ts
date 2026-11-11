export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: unknown,
  ) {
    super(apiMessage(payload, status));
    this.name = 'ApiError';
  }
}

let csrfToken = '';

function messagesFrom(value: unknown, prefix = ''): string[] {
  if (typeof value === 'string') return [prefix ? `${prefix}: ${value}` : value];
  if (Array.isArray(value)) return value.flatMap((item) => messagesFrom(item, prefix));
  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) => {
      if (key === 'detail' || key === 'regra' || key === 'non_field_errors') {
        return messagesFrom(child, prefix);
      }
      return messagesFrom(child, key.replaceAll('_', ' '));
    });
  }
  return [];
}

function apiMessage(payload: unknown, status: number): string {
  const messages = messagesFrom(payload);
  if (messages.length) return [...new Set(messages)].join(' ');
  if (status === 401) return 'Sua sessão expirou. Entre novamente.';
  if (status === 403) return 'Seu perfil não tem permissão para esta ação.';
  return 'Não foi possível concluir a solicitação.';
}

async function payloadFrom(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: text };
  }
}

export async function refreshCsrf(): Promise<void> {
  const response = await fetch('/api/auth/csrf/', {
    method: 'GET',
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  });
  const payload = await payloadFrom(response) as { csrfToken?: unknown } | null;
  if (!response.ok) throw new ApiError(response.status, payload);
  if (!payload || typeof payload.csrfToken !== 'string' || !payload.csrfToken) {
    throw new Error('A API não retornou o token de proteção da sessão.');
  }
  csrfToken = payload.csrfToken;
}

export function clearCsrf(): void {
  csrfToken = '';
}

export interface ApiOptions {
  method?: string;
  body?: unknown;
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase();
  const headers = new Headers({ Accept: 'application/json' });
  const safeMethods = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

  if (options.body !== undefined) headers.set('Content-Type', 'application/json');
  if (!safeMethods.has(method)) {
    if (!csrfToken) await refreshCsrf();
    headers.set('X-CSRFToken', csrfToken);
  }

  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const payload = await payloadFrom(response);
  if (!response.ok) throw new ApiError(response.status, payload);
  return payload as T;
}

