import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';
import { clearCsrf } from './api';
import type { Profile, Session } from './types';

/* Testes dos itens da revisão do cliente web (erros, funções que faltavam e usabilidade). */

const admin: Profile = { id: 1, nome: 'Carla Admin', email: 'a@example.com', perfil: 'ADMINISTRADOR', servicos: [] };

function session(status = 'AGENDADA'): Session {
  return {
    id: 10, titulo: 'Sessão da manhã', inicio: '2026-11-16T09:00:00Z', fim: '2026-11-16T10:00:00Z',
    servico: 3, participantes: [7], presencas: [{ aluno: 7, situacao_presenca: null }], status,
  };
}

function json(value: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(value) } as Response;
}

/** Simula a API com o Administrador autenticado. Rotas comuns já vêm preenchidas. */
function mockApi(routes: Record<string, () => Response>) {
  const padrao: Record<string, () => Response> = {
    'GET /api/sessoes/?': () => json([]),
    'GET /api/alunos/': () => json([]),
    'GET /api/servicos/': () => json([]),
    'GET /api/pendencias/': () => json({ total: 0, tipos: [], itens: [] }),
  };
  const todas = { ...padrao, ...routes };
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method ?? 'GET').toUpperCase();
    if (url === '/api/auth/session/') return json(admin);
    if (url === '/api/auth/csrf/') return json({ csrfToken: 'csrf' });
    const key = `${method} ${url.startsWith('/api/sessoes/?') ? '/api/sessoes/?' : url}`;
    const handler = todas[key];
    if (!handler) throw new Error(`Rota inesperada: ${key}`);
    return handler();
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function bodyOf(fetchMock: ReturnType<typeof mockApi>, method: string, url: string): unknown {
  const call = fetchMock.mock.calls.find(([input, init]) => String(input) === url && init?.method === method);
  return call?.[1]?.body ? JSON.parse(String(call[1].body)) : undefined;
}

beforeEach(() => {
  clearCsrf();
  vi.stubGlobal('confirm', () => true);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Revisão da interface', () => {
  it('mostra o contador de pendências no menu e abre a sessão pelo atalho', async () => {
    mockApi({
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'GET /api/pendencias/': () => json({
        total: 1,
        tipos: [{ valor: 'PRESENCA_PENDENTE', rotulo: 'Presença pendente' }],
        itens: [{
          tipo: 'PRESENCA_PENDENTE', motivo: '1 de 1 participante(s) sem presença ou falta registrada.',
          sessao: { id: 10, titulo: 'Sessão da manhã', inicio: '2026-11-16T09:00:00Z', fim: '2026-11-16T10:00:00Z', status: 'AGENDADA', servico: { id: 3, nome: 'Treino funcional', categoria: 'TREINO' } },
          responsavel: { id: 2, nome: 'Diego Treinador' },
        }],
      }),
      'GET /api/sessoes/10/': () => json(session()),
    });

    render(<App />);
    expect(await screen.findByLabelText('1 pendências')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /pendências/i }));
    fireEvent.click(await screen.findByRole('button', { name: 'Ver sessão' }));

    expect(await screen.findByText('Não registrada')).toBeTruthy();
    expect(screen.getByText('Ana Lima')).toBeTruthy();
    // O Administrador consulta, mas não registra presença.
    expect(screen.queryByRole('button', { name: 'Salvar presença' })).toBeNull();
  });

  it('Administrador abre os detalhes na agenda, vê o relatório e cancela a sessão', async () => {
    const fetchMock = mockApi({
      'GET /api/sessoes/?': () => json([session('REALIZADA')]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'GET /api/servicos/': () => json([{ id: 3, nome: 'Treino funcional', categoria: 'TREINO' }]),
      'GET /api/sessoes/10/relatorio/': () => json({ id: 1, sessao: 10, status: 'FINALIZADO', objetivo: 'Força', local: 'Sala 2', exercicios: 'Agachamento', volume_unidade: 'kg', data: '2026-11-16', horario: '10:00:00', volume_valor: '100.00', intensidade_borg: '6.0', finalizado_em: '2026-11-16T12:00:00Z' }),
      'PATCH /api/sessoes/10/': () => json(session('CANCELADA')),
    });

    render(<App />);
    expect(await screen.findByText('Treino funcional · 1 participante(s)')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Detalhes' }));
    expect(screen.queryByRole('button', { name: 'Marcar realizada' })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ver relatório' }));
    expect(await screen.findByText('Agachamento')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Cancelar sessão' }));
    expect(await screen.findByText('Esta sessão foi cancelada.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'PATCH', '/api/sessoes/10/')).toEqual({ status: 'CANCELADA' });
  });

  it('Cadastros listam, editam e mostram o 409 ao remover um aluno em uso', async () => {
    const fetchMock = mockApi({
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima', data_nascimento: '2010-03-01', telefone: '' }]),
      'PATCH /api/alunos/7/': () => json({ id: 7, nome: 'Ana Lima Souza', data_nascimento: '2010-03-01', telefone: '' }),
      'DELETE /api/alunos/7/': () => json({ detail: 'Este aluno participa de sessões. Remova-o das sessões antes de excluir o cadastro.' }, 409),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /cadastros/i }));
    expect(await screen.findByRole('rowheader', { name: 'Ana Lima' })).toBeTruthy();
    expect(screen.getByText('01/03/2010')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }));
    const nome = screen.getByLabelText('Nome completo') as HTMLInputElement;
    expect(nome.value).toBe('Ana Lima');
    fireEvent.change(nome, { target: { value: 'Ana Lima Souza' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Salvar alterações' }).closest('form')!);
    expect(await screen.findByText('Cadastro atualizado.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'PATCH', '/api/alunos/7/')).toEqual({ nome: 'Ana Lima Souza', data_nascimento: '2010-03-01', telefone: '' });

    fireEvent.click(screen.getByRole('button', { name: 'Remover' }));
    expect((await screen.findByRole('alert')).textContent).toContain('Operação recusada: Este aluno participa de sessões');
  });

  it('Novo agendamento confere fim depois do início e conta os alunos escolhidos', async () => {
    const fetchMock = mockApi({
      'GET /api/servicos/': () => json([{ id: 3, nome: 'Treino funcional', categoria: 'TREINO', profissionais_habilitados: [2] }]),
      'GET /api/profissionais/': () => json([{ id: 2, nome: 'Diego Treinador', perfil: 'TREINADOR' }]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /novo agendamento/i }));
    fireEvent.change(await screen.findByLabelText('Título'), { target: { value: 'Treino' } });
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Profissional'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Início'), { target: { value: '2026-11-16T10:00' } });
    fireEvent.change(screen.getByLabelText('Fim'), { target: { value: '2026-11-16T09:00' } });
    fireEvent.click(screen.getByLabelText('Ana Lima'));
    expect(screen.getByText(/1 selecionado \(máximo 6\)/)).toBeTruthy();

    fireEvent.submit(screen.getByRole('button', { name: /confirmar agendamento/i }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toBe('O fim precisa ser depois do início.');
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false);
  });

  it('Disponibilidade filtra por profissional e edita um período', async () => {
    const fetchMock = mockApi({
      'GET /api/profissionais/': () => json([{ id: 2, nome: 'Diego Treinador', perfil: 'TREINADOR' }, { id: 4, nome: 'Eva Fisio', perfil: 'PROFISSIONAL_SAUDE' }]),
      'GET /api/disponibilidades/': () => json([
        { id: 1, profissional: 2, inicio: '2026-11-16T08:00:00Z', fim: '2026-11-16T12:00:00Z' },
        { id: 2, profissional: 4, inicio: '2026-11-17T08:00:00Z', fim: '2026-11-17T12:00:00Z' },
      ]),
      'GET /api/bloqueios-agenda/': () => json([]),
      'PATCH /api/disponibilidades/1/': () => json({ id: 1, profissional: 2, inicio: '2026-11-16T08:00:00Z', fim: '2026-11-16T13:00:00Z' }),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /disponibilidade/i }));
    expect(await screen.findAllByRole('button', { name: 'Editar' })).toHaveLength(2);

    fireEvent.change(screen.getByLabelText('Profissional', { selector: '#range-filter-professional' }), { target: { value: '2' } });
    expect(screen.getAllByRole('button', { name: 'Editar' })).toHaveLength(1);

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }));
    fireEvent.submit(screen.getByRole('button', { name: /salvar alterações/i }).closest('form')!);
    expect(await screen.findByText('Período atualizado.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'PATCH', '/api/disponibilidades/1/')).toMatchObject({ profissional: 2 });
  });
});
