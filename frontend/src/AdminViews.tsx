import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from './api';
import { formatDate, formatDateTime, plural, reportError } from './errors';
import { SessionDetails } from './SessionActions';
import type { DashboardData, Notice, PendingList, Professional, ProfessionalServiceLink, Service, Session, Student } from './types';

interface AdminProps {
  onUnauthorized: () => void;
}

export function Message({ notice }: { notice: Notice | null }) {
  if (!notice) return null;
  const className = { error: 'error-message', info: 'info-message', success: 'success-message' }[notice.kind];
  return <div className={`inline-message ${className}`} role={notice.kind === 'error' ? 'alert' : 'status'}>{notice.message}</div>;
}

export function Loading({ text }: { text: string }) {
  return <div className="loading-card" role="status"><span className="spinner" /> {text}</div>;
}

/** Pendências operacionais da agenda (RF-09). */
export function Pendencias({ onUnauthorized }: AdminProps) {
  const [tipo, setTipo] = useState('');
  const [dados, setDados] = useState<PendingList | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<Notice | null>(null);
  // Atalho para os detalhes (D-15): a sessão aberta e os nomes dos alunos.
  const [aberta, setAberta] = useState<Session | null>(null);
  const [nomes, setNomes] = useState(new Map<number, string>());

  useEffect(() => {
    api<Student[]>('/api/alunos/')
      .then((lista) => setNomes(new Map(lista.map((aluno) => [aluno.id, aluno.nome]))))
      .catch(() => undefined);
  }, []);

  async function verSessao(id: number) {
    if (aberta?.id === id) {
      setAberta(null);
      return;
    }
    setMessage(null);
    try {
      setAberta(await api<Session>(`/api/sessoes/${id}/`));
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    }
  }

  useEffect(() => {
    let active = true;
    setLoading(true);
    setMessage(null);
    const query = tipo ? `?tipo=${tipo}` : '';
    api<PendingList>(`/api/pendencias/${query}`)
      .then((result) => { if (active) setDados(result); })
      .catch((error: unknown) => { if (active) reportError(error, onUnauthorized, setMessage); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [tipo, onUnauthorized]);

  return (
    <section className="content-panel" aria-labelledby="pending-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">ACOMPANHAMENTO</p><h2 id="pending-title">Pendências</h2><p className="muted">Sessões encerradas com presença ou relatório pendente.</p></div>
        <span className="date-chip">{dados ? `${dados.total} no total` : '…'}</span>
      </div>
      <div className="filter-bar">
        <div className="filter-field">
          <label htmlFor="pending-type">Tipo</label>
          <select id="pending-type" value={tipo} onChange={(event) => setTipo(event.target.value)}>
            <option value="">Todas</option>
            {dados?.tipos.map((item) => <option key={item.valor} value={item.valor}>{item.rotulo}</option>)}
          </select>
        </div>
      </div>
      <Message notice={message} />
      {loading && <Loading text="Carregando pendências…" />}
      {!loading && dados && dados.itens.length === 0 && (
        <div className="empty-state"><h3>Nenhuma pendência</h3><p>A agenda está em dia.</p></div>
      )}
      {!loading && dados && dados.itens.length > 0 && (
        <div className="session-list">
          {dados.itens.map((item) => (
            <article className="session-card" key={`${item.tipo}-${item.sessao.id}`}>
              <div className="session-time"><span className="session-date">{formatDateTime(item.sessao.fim)}</span>fim previsto</div>
              <div className="session-summary"><h4>{item.sessao.titulo}</h4><p>{item.motivo}</p><p>Responsável: {item.responsavel.nome}</p></div>
              <div className="session-meta">
                <span className="tag">{item.sessao.servico.nome}</span>
                <span className="tag status">{dados.tipos.find((t) => t.valor === item.tipo)?.rotulo ?? item.tipo}</span>
                <button className="button button-quiet" type="button" aria-expanded={aberta?.id === item.sessao.id} onClick={() => void verSessao(item.sessao.id)}>
                  {aberta?.id === item.sessao.id ? 'Fechar' : 'Ver sessão'}
                </button>
              </div>
              {aberta?.id === item.sessao.id && (
                <SessionDetails
                  session={aberta}
                  isTraining={item.sessao.servico.categoria === 'TREINO'}
                  studentNames={nomes}
                  onChanged={setAberta}
                  onUnauthorized={onUnauthorized}
                />
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

/** Dashboard por serviço e situação (RF-11). Sem datas, a API usa o mês atual. */
export function Dashboard({ onUnauthorized }: AdminProps) {
  const [inicio, setInicio] = useState('');
  const [fim, setFim] = useState('');
  const [dados, setDados] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);

  async function carregar(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      // Envia as datas preenchidas; a regra "início e fim juntos" é conferida pela API.
      const params = new URLSearchParams();
      if (inicio) params.set('inicio', inicio);
      if (fim) params.set('fim', fim);
      const query = params.size ? `?${params.toString()}` : '';
      const resultado = await api<DashboardData>(`/api/dashboard/${query}`);
      setDados(resultado);
      // Mostra nos campos o período usado pela API (na primeira carga, o mês atual).
      setInicio(resultado.periodo.inicio);
      setFim(resultado.periodo.fim);
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void carregar(); }, []); // Primeira carga: mês atual.

  return (
    <section className="content-panel" aria-labelledby="dashboard-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">VISÃO GERAL</p><h2 id="dashboard-title">Dashboard</h2><p className="muted">Compromissos por serviço e situação no período.</p></div>
        {dados && <span className="date-chip">{formatDate(dados.periodo.inicio)} a {formatDate(dados.periodo.fim)}</span>}
      </div>
      <form className="filter-bar" onSubmit={(event) => void carregar(event)}>
        <div className="filter-field"><label htmlFor="dash-start">De</label><input id="dash-start" type="date" value={inicio} onChange={(event) => setInicio(event.target.value)} /></div>
        <div className="filter-field"><label htmlFor="dash-end">Até</label><input id="dash-end" type="date" value={fim} onChange={(event) => setFim(event.target.value)} /></div>
        <button className="button button-primary" type="submit" disabled={loading}>Atualizar</button>
      </form>
      <Message notice={message} />
      {loading && <Loading text="Carregando dashboard…" />}
      {!loading && dados && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr><th scope="col">Serviço</th>{dados.situacoes.map((s) => <th scope="col" key={s.valor}>{s.rotulo}</th>)}<th scope="col">Total</th></tr>
            </thead>
            <tbody>
              {dados.servicos.map((linha) => (
                <tr key={linha.id}>
                  <th scope="row">{linha.nome}</th>
                  {dados.situacoes.map((s) => <td key={s.valor}>{linha.por_situacao[s.valor] ?? 0}</td>)}
                  <td>{linha.total}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th scope="row">Total</th>
                {dados.situacoes.map((s) => <td key={s.valor}>{dados.total.por_situacao[s.valor] ?? 0}</td>)}
                <td>{dados.total.total}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </section>
  );
}

/** Confirmação de agendamento (UC-05). Conflitos e capacidade são validados pela API (409). */
export function NovoAgendamento({ onUnauthorized, onManageLinks }: AdminProps & { onManageLinks: () => void }) {
  const [servicos, setServicos] = useState<Service[]>([]);
  const [profissionais, setProfissionais] = useState<Professional[]>([]);
  const [alunos, setAlunos] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);
  const [servicoSelecionado, setServicoSelecionado] = useState('');
  const [profissionalSelecionado, setProfissionalSelecionado] = useState('');
  const [selecionados, setSelecionados] = useState(0);

  const profissionaisElegiveis = servicos.find((servico) => String(servico.id) === servicoSelecionado)
    ?.profissionais_habilitados ?? [];
  const profissionaisDoServico = profissionais.filter(
    (profissional) => profissionaisElegiveis.includes(profissional.id),
  );

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Service[]>('/api/servicos/'),
      api<Professional[]>('/api/profissionais/'),
      api<Student[]>('/api/alunos/'),
    ])
      .then(([listaServicos, listaProfissionais, listaAlunos]) => {
        if (!active) return;
        setServicos(listaServicos);
        setProfissionais(listaProfissionais);
        setAlunos(listaAlunos);
      })
      .catch((error: unknown) => { if (active) reportError(error, onUnauthorized, setMessage); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [onUnauthorized]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const dados = new FormData(form);
    setMessage(null);
    setBusy(true);
    try {
      await api('/api/sessoes/', {
        method: 'POST',
        body: {
          titulo: String(dados.get('titulo')).trim(),
          tipo: dados.get('tipo'),
          servico: Number(dados.get('servico')),
          profissional: Number(dados.get('profissional')),
          inicio: new Date(String(dados.get('inicio'))).toISOString(),
          fim: new Date(String(dados.get('fim'))).toISOString(),
          participantes: dados.getAll('participantes').map(Number),
        },
      });
      form.reset();
      setServicoSelecionado('');
      setProfissionalSelecionado('');
      setSelecionados(0);
      setMessage({ kind: 'success', message: 'Agendamento confirmado.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="content-panel" aria-labelledby="booking-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">AGENDA</p><h2 id="booking-title">Novo agendamento</h2><p className="muted">A API confere horário, disponibilidade e limite de alunos.</p></div>
      </div>
      <Message notice={message} />
      {loading ? <Loading text="Carregando cadastros…" /> : (
        <form className="record-form" onSubmit={(event) => void submit(event)}>
          <div className="form-grid">
            <label htmlFor="booking-name">Título<input id="booking-name" name="titulo" required maxLength={150} /></label>
            <label htmlFor="booking-service">Serviço
              <select id="booking-service" name="servico" required value={servicoSelecionado} onChange={(event) => {
                setServicoSelecionado(event.target.value);
                setProfissionalSelecionado('');
              }}>
                <option value="" disabled>Selecione</option>
                {servicos.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
              </select>
            </label>
            <label htmlFor="booking-professional">Profissional
              <select id="booking-professional" name="profissional" required value={profissionalSelecionado} disabled={!servicoSelecionado || profissionaisDoServico.length === 0} onChange={(event) => setProfissionalSelecionado(event.target.value)}>
                <option value="" disabled>Selecione</option>
                {profissionaisDoServico.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </select>
            </label>
            <label htmlFor="booking-start">Início<input id="booking-start" name="inicio" type="datetime-local" required /></label>
            <label htmlFor="booking-end">Fim<input id="booking-end" name="fim" type="datetime-local" required /></label>
            <label htmlFor="booking-type">Formato da sessão
              <select id="booking-type" name="tipo" defaultValue="TREINAMENTO">
                <option value="TREINAMENTO">Treinamento</option>
                <option value="AVALIACAO">Avaliação</option>
              </select>
            </label>
          </div>
          {servicoSelecionado && profissionaisDoServico.length === 0 && (
            <p className="form-hint" role="status">
              Nenhum profissional está habilitado para este serviço.{' '}
              <button className="text-button" type="button" onClick={onManageLinks}>Configurar habilitações</button>
            </p>
          )}
          <fieldset className="checkbox-list" onChange={(event) => setSelecionados(event.currentTarget.querySelectorAll('input:checked').length)}>
            <legend>Alunos participantes · {plural(selecionados, 'selecionado', 'selecionados')} (máximo 6)</legend>
            {alunos.length === 0 && <p className="muted">Nenhum aluno cadastrado.</p>}
            {alunos.map((aluno) => (
              <label key={aluno.id}><input type="checkbox" name="participantes" value={aluno.id} /> {aluno.nome}</label>
            ))}
          </fieldset>
          <button className="button button-primary" type="submit" disabled={busy || !servicoSelecionado || !profissionalSelecionado}>{busy ? 'Confirmando…' : 'Confirmar agendamento'}</button>
        </form>
      )}
    </section>
  );
}

/** Configura as habilitações usadas pelo RN-04 e pelo filtro do agendamento. */
export function VinculosProfissionais({ onUnauthorized }: AdminProps) {
  const [servicos, setServicos] = useState<Service[]>([]);
  const [profissionais, setProfissionais] = useState<Professional[]>([]);
  const [vinculos, setVinculos] = useState<ProfessionalServiceLink[]>([]);
  const [servicoSelecionado, setServicoSelecionado] = useState('');
  const [profissionalSelecionado, setProfissionalSelecionado] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Service[]>('/api/servicos/'),
      api<Professional[]>('/api/profissionais/'),
      api<ProfessionalServiceLink[]>('/api/profissionais-servicos/'),
    ])
      .then(([listaServicos, listaProfissionais, listaVinculos]) => {
        if (!active) return;
        setServicos(listaServicos);
        setProfissionais(listaProfissionais);
        setVinculos(listaVinculos);
      })
      .catch((error: unknown) => { if (active) reportError(error, onUnauthorized, setMessage); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [onUnauthorized]);

  async function criarVinculo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const novo = await api<ProfessionalServiceLink>('/api/profissionais-servicos/', {
        method: 'POST',
        body: { profissional: Number(profissionalSelecionado), servico: Number(servicoSelecionado) },
      });
      setVinculos((atuais) => [...atuais, novo]);
      setProfissionalSelecionado('');
      setMessage({ kind: 'success', message: 'Habilitação cadastrada.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  async function removerVinculo(vinculo: ProfessionalServiceLink) {
    const profissional = profissionais.find((item) => item.id === vinculo.profissional)?.nome ?? 'profissional';
    const servico = servicos.find((item) => item.id === vinculo.servico)?.nome ?? 'serviço';
    if (!window.confirm(`Remover a habilitação de ${profissional} para ${servico}?`)) return;
    setBusy(true);
    setMessage(null);
    try {
      await api(`/api/profissionais-servicos/${vinculo.id}/`, { method: 'DELETE' });
      setVinculos((atuais) => atuais.filter((item) => item.id !== vinculo.id));
      setMessage({ kind: 'success', message: 'Habilitação removida.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  const profissionaisDisponiveis = profissionais.filter((profissional) =>
    !vinculos.some((vinculo) => vinculo.servico === Number(servicoSelecionado) && vinculo.profissional === profissional.id),
  );

  return (
    <section className="content-panel" aria-labelledby="links-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">CADASTROS</p><h2 id="links-title">Habilitações</h2><p className="muted">Defina quais profissionais podem atender cada serviço.</p></div>
      </div>
      <Message notice={message} />
      {loading ? <Loading text="Carregando profissionais e serviços…" /> : (
        <>
          <form className="record-form" onSubmit={(event) => void criarVinculo(event)}>
            <div className="form-grid">
              <label htmlFor="link-service">Serviço
                <select id="link-service" required value={servicoSelecionado} onChange={(event) => {
                  setServicoSelecionado(event.target.value);
                  setProfissionalSelecionado('');
                }}>
                  <option value="" disabled>Selecione</option>
                  {servicos.map((servico) => <option key={servico.id} value={servico.id}>{servico.nome}</option>)}
                </select>
              </label>
              <label htmlFor="link-professional">Profissional
                <select id="link-professional" required value={profissionalSelecionado} disabled={!servicoSelecionado || profissionaisDisponiveis.length === 0} onChange={(event) => setProfissionalSelecionado(event.target.value)}>
                  <option value="" disabled>Selecione</option>
                  {profissionaisDisponiveis.map((profissional) => <option key={profissional.id} value={profissional.id}>{profissional.nome} · {profissional.perfil === 'TREINADOR' ? 'Treinador' : 'Profissional de Saúde'}</option>)}
                </select>
              </label>
            </div>
            {servicoSelecionado && profissionaisDisponiveis.length === 0 && <p className="form-hint">Todos os profissionais já estão habilitados para este serviço.</p>}
            <button className="button button-primary" type="submit" disabled={busy || !servicoSelecionado || !profissionalSelecionado}>{busy ? 'Salvando…' : 'Adicionar habilitação'}</button>
          </form>
          <div className="table-scroll">
            <table className="data-table">
              <thead><tr><th scope="col">Serviço</th><th scope="col">Profissional</th><th scope="col">Perfil</th><th scope="col">Ação</th></tr></thead>
              <tbody>
                {vinculos.map((vinculo) => {
                  const profissional = profissionais.find((item) => item.id === vinculo.profissional);
                  const servico = servicos.find((item) => item.id === vinculo.servico);
                  if (!profissional || !servico) return null;
                  return <tr key={vinculo.id}>
                    <th scope="row">{servico.nome}</th><td>{profissional.nome}</td>
                    <td>{profissional.perfil === 'TREINADOR' ? 'Treinador' : 'Profissional de Saúde'}</td>
                    <td><button className="text-button danger-text" type="button" disabled={busy} onClick={() => void removerVinculo(vinculo)}>Remover</button></td>
                  </tr>;
                })}
                {vinculos.length === 0 && <tr><td colSpan={4}>Nenhuma habilitação cadastrada.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
