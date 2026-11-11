import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';
import { clearCsrf } from './api';
import type { Profile, Session } from './types';

const admin: Profile = { id: 1, nome: 'Carla Admin', email: 'a@example.com', perfil: 'ADMINISTRADOR', servicos: [] };
const trainer: Profile = {
  id: 2, nome: 'Diego Treinador', email: 't@example.com', perfil: 'TREINADOR',
  servicos: [{ id: 3, nome: 'Treino funcional', categoria: 'TREINO' }],
};
const health: Profile = {
  id: 4, nome: 'Eva Fisio', email: 'f@example.com', perfil: 'PROFISSIONAL_SAUDE',
  servicos: [{ id: 5, nome: 'Fisioterapia', categoria: 'FISIOTERAPIA' }],
};

function session(servico: number): Session {
  return {
    id: 10, titulo: 'Sessão da manhã', inicio: '2026-11-16T09:00:00Z', fim: '2026-11-16T10:00:00Z',
    servico, profissional: 2, participantes: [7], presencas: [{ aluno: 7, situacao_presenca: null }], status: 'AGENDADA',
  };
}

function json(value: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, text: async () => JSON.stringify(value) } as Response;
}

type Handler = (body: unknown) => Response;

/** Simula a API: a sessão já está autenticada e cada rota "MÉTODO url" tem uma resposta. */
function mockApi(profile: Profile, routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method ?? 'GET').toUpperCase();
    if (url === '/api/auth/session/') return json(profile);
    if (url === '/api/auth/csrf/') return json({ csrfToken: 'csrf' });
    const key = `${method} ${url.startsWith('/api/sessoes/?') ? '/api/sessoes/?' : url}`;
    const handler = routes[key];
    if (!handler) throw new Error(`Rota inesperada: ${key}`);
    return handler(init?.body ? JSON.parse(String(init.body)) : undefined);
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function bodyOf(fetchMock: ReturnType<typeof mockApi>, method: string, url: string): unknown {
  const call = fetchMock.mock.calls.find(([input, init]) => String(input) === url && init?.method === method);
  return call?.[1]?.body ? JSON.parse(String(call[1].body)) : undefined;
}

beforeEach(() => clearCsrf());
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Administrador', () => {
  it('consulta pendências e filtra por tipo', async () => {
    const pendencias = {
      total: 1,
      tipos: [{ valor: 'PRESENCA_PENDENTE', rotulo: 'Presença pendente' }, { valor: 'RELATORIO_PENDENTE', rotulo: 'Relatório pendente' }],
      itens: [{
        tipo: 'PRESENCA_PENDENTE', motivo: '1 de 1 participante(s) sem presença ou falta registrada.',
        sessao: { id: 10, titulo: 'Treino de força', inicio: '2026-11-16T09:00:00Z', fim: '2026-11-16T10:00:00Z', status: 'AGENDADA', servico: { id: 3, nome: 'Treino funcional', categoria: 'TREINO' } },
        responsavel: { id: 2, nome: 'Diego Treinador' },
      }],
    };
    const fetchMock = mockApi(admin, {
      'GET /api/sessoes/?': () => json([]),
      'GET /api/pendencias/': () => json(pendencias),
      'GET /api/pendencias/?tipo=RELATORIO_PENDENTE': () => json({ ...pendencias, itens: [] }),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /pendências/i }));

    expect(await screen.findByText('Treino de força')).toBeTruthy();
    expect(screen.getByText('Responsável: Diego Treinador')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Tipo'), { target: { value: 'RELATORIO_PENDENTE' } });
    expect(await screen.findByText('Nenhuma pendência')).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith('/api/pendencias/?tipo=RELATORIO_PENDENTE', expect.anything());
  });

  it('vê o dashboard por serviço e situação', async () => {
    mockApi(admin, {
      'GET /api/sessoes/?': () => json([]),
      'GET /api/dashboard/': () => json({
        periodo: { inicio: '2026-11-01', fim: '2026-11-30' },
        situacoes: [{ valor: 'AGENDADA', rotulo: 'Agendada' }, { valor: 'REALIZADA', rotulo: 'Realizada' }],
        servicos: [{ id: 3, nome: 'Treino funcional', por_situacao: { AGENDADA: 2, REALIZADA: 1 }, total: 3 }],
        total: { por_situacao: { AGENDADA: 2, REALIZADA: 1 }, total: 3 },
      }),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /dashboard/i }));

    const table = await screen.findByRole('table');
    expect(within(table).getByRole('rowheader', { name: 'Treino funcional' })).toBeTruthy();
    expect(within(table).getAllByText('3')).toHaveLength(2);
    expect(screen.getByText('2026-11-01 a 2026-11-30')).toBeTruthy();
  });

  it('consulta os treinadores e relaciona os treinos agendados a cada responsável', async () => {
    const adminWithTrainingService = { ...admin, servicos: [{ id: 3, nome: 'Treino funcional', categoria: 'TREINO' }] };
    mockApi(adminWithTrainingService, {
      'GET /api/sessoes/?': () => json([session(3)]),
      'GET /api/profissionais/': () => json([
        { id: 2, nome: 'Diego Treinador', email: 'diego@example.com', perfil: 'TREINADOR' },
        { id: 4, nome: 'Eva Fisio', email: 'eva@example.com', perfil: 'PROFISSIONAL_SAUDE' },
      ]),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /equipe e treinos/i }));

    expect(await screen.findByRole('heading', { name: 'Treinadores e treinos' })).toBeTruthy();
    expect(screen.getAllByText('Diego Treinador')).toHaveLength(2);
    expect(screen.queryByText('Eva Fisio')).toBeNull();
    expect(screen.getByText('Sessão da manhã')).toBeTruthy();
    expect(screen.getByText('Diego Treinador', { selector: 'strong' })).toBeTruthy();
  });

  it('mostra a recusa 409 ao confirmar agendamento', async () => {
    mockApi(admin, {
      'GET /api/sessoes/?': () => json([]),
      'GET /api/servicos/': () => json([{ id: 3, nome: 'Treino funcional', categoria: 'TREINO', profissionais_habilitados: [2] }]),
      'GET /api/profissionais/': () => json([{ id: 2, nome: 'Diego Treinador', perfil: 'TREINADOR' }]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'POST /api/sessoes/': () => json({ regra: 'RN-01', detail: 'O profissional já possui um compromisso neste horário.' }, 409),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /novo agendamento/i }));
    fireEvent.change(await screen.findByLabelText('Título'), { target: { value: 'Treino' } });
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Profissional'), { target: { value: '2' } });
    fireEvent.change(screen.getByLabelText('Início'), { target: { value: '2026-11-16T09:00' } });
    fireEvent.change(screen.getByLabelText('Fim'), { target: { value: '2026-11-16T10:00' } });
    fireEvent.click(screen.getByLabelText('Ana Lima'));
    fireEvent.submit(screen.getByRole('button', { name: /confirmar agendamento/i }).closest('form')!);

    expect((await screen.findByRole('alert')).textContent)
      .toBe('Operação recusada: RN-01 O profissional já possui um compromisso neste horário.');
  });

  it('filtra os profissionais pelas habilitações do serviço selecionado', async () => {
    mockApi(admin, {
      'GET /api/sessoes/?': () => json([]),
      'GET /api/servicos/': () => json([
        { id: 3, nome: 'Treino funcional', categoria: 'TREINO', profissionais_habilitados: [2] },
        { id: 5, nome: 'Fisioterapia', categoria: 'FISIOTERAPIA', profissionais_habilitados: [4] },
      ]),
      'GET /api/profissionais/': () => json([
        { id: 2, nome: 'Diego Treinador', perfil: 'TREINADOR' },
        { id: 4, nome: 'Eva Fisio', perfil: 'PROFISSIONAL_SAUDE' },
      ]),
      'GET /api/alunos/': () => json([]),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: /novo agendamento/i }));
    const profissional = await screen.findByLabelText('Profissional') as HTMLSelectElement;
    expect(profissional.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '3' } });
    expect(within(profissional).getByRole('option', { name: 'Diego Treinador' })).toBeTruthy();
    expect(within(profissional).queryByRole('option', { name: 'Eva Fisio' })).toBeNull();
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '5' } });
    expect(within(profissional).getByRole('option', { name: 'Eva Fisio' })).toBeTruthy();
    expect(within(profissional).queryByRole('option', { name: 'Diego Treinador' })).toBeNull();
  });

  it('cadastra e remove habilitações pela interface administrativa', async () => {
    const fetchMock = mockApi(admin, {
      'GET /api/sessoes/?': () => json([]),
      'GET /api/servicos/': () => json([{ id: 3, nome: 'Treino funcional', categoria: 'TREINO', profissionais_habilitados: [] }]),
      'GET /api/profissionais/': () => json([{ id: 2, nome: 'Diego Treinador', perfil: 'TREINADOR' }]),
      'GET /api/profissionais-servicos/': () => json([]),
      'POST /api/profissionais-servicos/': (body) => json({ id: 8, ...(body as object) }, 201),
      'DELETE /api/profissionais-servicos/8/': () => json(null, 204),
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Habilitações' }));
    expect(await screen.findByRole('heading', { name: 'Habilitações' })).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Profissional'), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar habilitação' }));

    expect(await screen.findByText('Habilitação cadastrada.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'POST', '/api/profissionais-servicos/')).toEqual({ profissional: 2, servico: 3 });
    fireEvent.click(screen.getByRole('button', { name: 'Remover' }));
    expect(await screen.findByText('Habilitação removida.')).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith('/api/profissionais-servicos/8/', expect.objectContaining({ method: 'DELETE' }));
  });
});

describe('Treinador', () => {
  it('registra presença, vê a recusa 409 da situação e finaliza o relatório', async () => {
    const atualizada = { ...session(3), presencas: [{ aluno: 7, situacao_presenca: 'PRESENTE' }] };
    const fetchMock = mockApi(trainer, {
      'GET /api/sessoes/?': () => json([session(3)]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'PATCH /api/sessoes/10/presencas/': () => json(atualizada),
      'PATCH /api/sessoes/10/': () => json({ detail: 'A presença e a situação da sessão só podem ser registradas a partir do fim previsto.' }, 409),
      'GET /api/sessoes/10/relatorio/': () => json({ detail: 'Esta sessão ainda não possui relatório de treino.' }, 404),
      'POST /api/sessoes/10/relatorio/': () => json({ id: 1, sessao: 10, status: 'RASCUNHO', objetivo: 'Força', local: '', exercicios: '', volume_unidade: '', data: null, horario: null, volume_valor: null, intensidade_borg: null, finalizado_em: null }, 201),
      'POST /api/sessoes/10/relatorio/finalizar/': () => json({ id: 1, sessao: 10, status: 'FINALIZADO', objetivo: 'Força', local: 'Sala 2', exercicios: 'Agachamento', volume_unidade: 'kg', data: '2026-11-16', horario: '10:00:00', volume_valor: '100.00', intensidade_borg: '6.0', finalizado_em: '2026-11-16T12:00:00Z' }),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Detalhes' }));

    fireEvent.change(await screen.findByLabelText('Ana Lima'), { target: { value: 'PRESENTE' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Salvar presença' }).closest('form')!);
    expect(await screen.findByText('Presença registrada.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'PATCH', '/api/sessoes/10/presencas/')).toEqual({ presencas: [{ aluno: 7, situacao: 'PRESENTE' }] });

    fireEvent.click(screen.getByRole('button', { name: 'Marcar realizada' }));
    expect(await screen.findByText(/Operação recusada: A presença e a situação/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Abrir relatório' }));
    expect(await screen.findByText(/ainda não tem relatório/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Objetivo'), { target: { value: 'Força' } });
    fireEvent.click(screen.getByRole('button', { name: 'Salvar rascunho' }));
    expect(await screen.findByText('Rascunho salvo.')).toBeTruthy();
    expect(bodyOf(fetchMock, 'POST', '/api/sessoes/10/relatorio/')).toEqual({ objetivo: 'Força' });

    fireEvent.click(screen.getByRole('button', { name: 'Finalizar relatório' }));
    expect(await screen.findByText('Relatório finalizado.')).toBeTruthy();
    expect(screen.getByText('Finalizado')).toBeTruthy();
  });

  it('volta ao login quando a sessão expira (401) durante uma ação', async () => {
    mockApi(trainer, {
      'GET /api/sessoes/?': () => json([session(3)]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'PATCH /api/sessoes/10/': () => json({ detail: 'Autenticação necessária.' }, 401),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Detalhes' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Marcar realizada' }));

    expect(await screen.findByRole('heading', { name: 'Entrar na sua conta' })).toBeTruthy();
    expect(screen.getByText('Sua sessão expirou. Entre novamente.')).toBeTruthy();
  });
});

describe('Profissional de Saúde', () => {
  it('registra presença sem acesso a situação nem relatório, e vê o 403 da API', async () => {
    mockApi(health, {
      'GET /api/sessoes/?': () => json([session(5)]),
      'GET /api/alunos/': () => json([{ id: 7, nome: 'Ana Lima' }]),
      'PATCH /api/sessoes/10/presencas/': () => json({ detail: 'Apenas o profissional responsável pela sessão registra presença ou falta.' }, 403),
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Detalhes' }));
    expect(screen.queryByRole('button', { name: /pendências/i })).toBeNull();

    expect(screen.queryByRole('button', { name: 'Marcar realizada' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Abrir relatório' })).toBeNull();
    fireEvent.change(await screen.findByLabelText('Ana Lima'), { target: { value: 'FALTA' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Salvar presença' }).closest('form')!);

    expect((await screen.findByRole('alert')).textContent).toContain('Acesso negado: Apenas o profissional responsável');
  });

  it('avisa sobre falha de rede ao carregar a agenda', async () => {
    mockApi(health, {
      'GET /api/sessoes/?': () => { throw new TypeError('Failed to fetch'); },
      'GET /api/alunos/': () => json([]),
    });

    render(<App />);

    expect((await screen.findByRole('alert')).textContent).toBe('Falha de conexão. Verifique a rede e tente novamente.');
  });
});
