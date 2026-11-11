import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from './api';
import { formatDateTime, reportError } from './errors';
import type { DashboardData, Notice, PendingList, Professional, Service, Student } from './types';

interface AdminProps {
  onUnauthorized: () => void;
}

export function Message({ notice }: { notice: Notice | null }) {
  if (!notice) return null;
  const className = notice.kind === 'error' ? 'error-message' : 'success-message';
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
              </div>
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
      const query = inicio || fim ? `?${new URLSearchParams({ inicio, fim }).toString()}` : '';
      setDados(await api<DashboardData>(`/api/dashboard/${query}`));
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
        {dados && <span className="date-chip">{dados.periodo.inicio} a {dados.periodo.fim}</span>}
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
export function NovoAgendamento({ onUnauthorized }: AdminProps) {
  const [servicos, setServicos] = useState<Service[]>([]);
  const [profissionais, setProfissionais] = useState<Professional[]>([]);
  const [alunos, setAlunos] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);

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
            <label htmlFor="booking-type">Tipo
              <select id="booking-type" name="tipo" defaultValue="TREINAMENTO">
                <option value="TREINAMENTO">Treinamento</option>
                <option value="AVALIACAO">Avaliação</option>
              </select>
            </label>
            <label htmlFor="booking-service">Serviço
              <select id="booking-service" name="servico" required defaultValue="">
                <option value="" disabled>Selecione</option>
                {servicos.map((s) => <option key={s.id} value={s.id}>{s.nome}</option>)}
              </select>
            </label>
            <label htmlFor="booking-professional">Profissional
              <select id="booking-professional" name="profissional" required defaultValue="">
                <option value="" disabled>Selecione</option>
                {profissionais.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </select>
            </label>
            <label htmlFor="booking-start">Início<input id="booking-start" name="inicio" type="datetime-local" required /></label>
            <label htmlFor="booking-end">Fim<input id="booking-end" name="fim" type="datetime-local" required /></label>
          </div>
          <fieldset className="checkbox-list">
            <legend>Alunos participantes</legend>
            {alunos.length === 0 && <p className="muted">Nenhum aluno cadastrado.</p>}
            {alunos.map((aluno) => (
              <label key={aluno.id}><input type="checkbox" name="participantes" value={aluno.id} /> {aluno.nome}</label>
            ))}
          </fieldset>
          <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Confirmando…' : 'Confirmar agendamento'}</button>
        </form>
      )}
    </section>
  );
}
