import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { clearCsrf } from './api';
import type { Profile } from './types';

const trainer: Profile = {
  id: 12,
  nome: 'Treinador Teste',
  email: 'treinador@example.com',
  perfil: 'TREINADOR',
  servicos: [{ id: 3, nome: 'Treino funcional', categoria: 'TREINO' }],
};

const administrator: Profile = {
  id: 1,
  nome: 'Admin Teste',
  email: 'admin@example.com',
  perfil: 'ADMINISTRADOR',
  servicos: [{ id: 3, nome: 'Treino funcional', categoria: 'TREINO' }],
};

function jsonResponse(value: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(value),
  } as Response;
}

function unauthenticatedSession() {
  return jsonResponse({ detail: 'Autenticação necessária.' }, 401);
}

beforeEach(() => {
  clearCsrf();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  clearCsrf();
});

describe('cliente web GAAP', () => {
  it('autentica e abre a agenda permitida ao Treinador', async () => {
    let sessionCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url === '/api/auth/session/') {
        sessionCalls += 1;
        return sessionCalls === 1 ? unauthenticatedSession() : jsonResponse(trainer);
      }
      if (url === '/api/auth/csrf/') return jsonResponse({ csrfToken: 'token-csrf' });
      if (url === '/api/auth/login/') return jsonResponse({ perfil: trainer.perfil });
      if (url.startsWith('/api/sessoes/')) return jsonResponse([]);
      throw new Error(`Endpoint inesperado: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);
    await screen.findByRole('heading', { name: 'Entrar na sua conta' });
    fireEvent.change(screen.getByLabelText('Login ou e-mail'), { target: { value: 'treinador@example.com' } });
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'senha-teste' } });
    fireEvent.submit(screen.getByRole('button', { name: /entrar/i }).closest('form')!);

    expect(await screen.findByRole('heading', { name: 'Olá, Treinador Teste' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /cadastros/i })).toBeNull();
    expect(screen.getByRole('heading', { name: 'Agenda' })).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/^\/api\/sessoes\//),
      expect.objectContaining({ credentials: 'same-origin' }),
    ));
    const loginCall = fetchMock.mock.calls.find(([input]) => String(input) === '/api/auth/login/');
    expect(loginCall).toBeTruthy();
    const headers = new Headers(loginCall?.[1]?.headers);
    expect(headers.get('X-CSRFToken')).toBe('token-csrf');
  });

  it('mostra Cadastros apenas ao Administrador e valida o envio pela API', async () => {
    let sessionCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url === '/api/auth/session/') {
        sessionCalls += 1;
        return sessionCalls === 1 ? unauthenticatedSession() : jsonResponse(administrator);
      }
      if (url === '/api/auth/csrf/') return jsonResponse({ csrfToken: 'token-csrf' });
      if (url === '/api/auth/login/') return jsonResponse({ perfil: administrator.perfil });
      if (url.startsWith('/api/sessoes/')) return jsonResponse([]);
      if (url === '/api/alunos/') return jsonResponse({ id: 8, nome: 'Ana Lima' }, 201);
      throw new Error(`Endpoint inesperado: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);
    await screen.findByRole('heading', { name: 'Entrar na sua conta' });
    fireEvent.change(screen.getByLabelText('Login ou e-mail'), { target: { value: 'admin@example.com' } });
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'senha-teste' } });
    fireEvent.submit(screen.getByRole('button', { name: /entrar/i }).closest('form')!);
    fireEvent.click(await screen.findByRole('button', { name: /cadastros/i }));

    expect(screen.getByRole('heading', { name: 'Cadastros' })).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Nome completo'), { target: { value: 'Ana Lima' } });
    fireEvent.change(screen.getByLabelText('Data de nascimento'), { target: { value: '2010-03-01' } });
    fireEvent.submit(screen.getByRole('button', { name: /salvar aluno/i }).closest('form')!);

    expect(await screen.findByText('Cadastro salvo com sucesso.')).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith('/api/alunos/', expect.objectContaining({
      method: 'POST',
      credentials: 'same-origin',
      headers: expect.any(Headers),
      body: JSON.stringify({ nome: 'Ana Lima', data_nascimento: '2010-03-01', telefone: '' }),
    }));
  });

  it('apresenta erro de credenciais sem expor se a conta existe', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url === '/api/auth/session/') return unauthenticatedSession();
      if (url === '/api/auth/csrf/') return jsonResponse({ csrfToken: 'token-csrf' });
      if (url === '/api/auth/login/') return jsonResponse({ detail: 'Login/e-mail ou senha incorretos.' }, 401);
      throw new Error(`Endpoint inesperado: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<App />);
    await screen.findByRole('heading', { name: 'Entrar na sua conta' });
    fireEvent.change(screen.getByLabelText('Login ou e-mail'), { target: { value: 'inexistente' } });
    fireEvent.change(screen.getByLabelText('Senha'), { target: { value: 'incorreta' } });
    fireEvent.submit(screen.getByRole('button', { name: /entrar/i }).closest('form')!);

    expect((await screen.findByRole('alert')).textContent).toContain('Login/e-mail ou senha incorretos.');
    expect(screen.queryByRole('heading', { name: /Olá,/ })).toBeNull();
  });
});

