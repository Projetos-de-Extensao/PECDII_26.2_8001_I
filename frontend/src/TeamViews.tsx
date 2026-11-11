import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from './api';
import { Loading, Message } from './AdminViews';
import { formatDateTime, reportError } from './errors';
import type { AgendaRange, Notice, Professional, Profile, Session, SessionList } from './types';

interface Props {
  onUnauthorized: () => void;
}

function dateString(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function localIso(value: string, nextDay = false): string {
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day + (nextDay ? 1 : 0));
  const minutes = -date.getTimezoneOffset();
  const sign = minutes >= 0 ? '+' : '-';
  const offsetHours = String(Math.floor(Math.abs(minutes) / 60)).padStart(2, '0');
  const offsetMinutes = String(Math.abs(minutes) % 60).padStart(2, '0');
  return `${dateString(date)}T00:00:00${sign}${offsetHours}:${offsetMinutes}`;
}

function sessionRows(payload: Session[] | SessionList): Session[] {
  return Array.isArray(payload) ? payload : payload.results ?? [];
}

/** Lista os Treinadores e os treinos agendados no período consultado. */
export function EquipeTreinos({ profile, onUnauthorized }: Props & { profile: Profile }) {
  const today = new Date();
  const [inicio, setInicio] = useState(dateString(today));
  const [fim, setFim] = useState(dateString(new Date(today.getFullYear(), today.getMonth(), today.getDate() + 30)));
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<Notice | null>(null);

  const load = useCallback(async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!inicio || !fim || fim < inicio) {
      setMessage({ kind: 'error', message: 'Informe um período válido.' });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const query = new URLSearchParams({ inicio: localIso(inicio), fim: localIso(fim, true) });
      const [people, agenda] = await Promise.all([
        api<Professional[]>('/api/profissionais/'),
        api<Session[] | SessionList>(`/api/sessoes/?${query}`),
      ]);
      setProfessionals(people);
      setSessions(sessionRows(agenda));
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
      setProfessionals([]);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, [fim, inicio, onUnauthorized]);

  useEffect(() => { void load(); }, []); // A primeira consulta cobre os próximos 30 dias.

  const trainers = professionals.filter((item) => item.perfil === 'TREINADOR').sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
  const trainersById = new Map(trainers.map((item) => [item.id, item]));
  const servicesById = new Map(profile.servicos.map((item) => [item.id, item]));
  const trainings = sessions
    .filter((item) => item.status === 'AGENDADA'
      && new Date(item.inicio).getTime() >= Date.now()
      && servicesById.get(item.servico ?? -1)?.categoria === 'TREINO'
      && trainersById.has(item.profissional ?? -1))
    .sort((a, b) => a.inicio.localeCompare(b.inicio));
  const countByTrainer = new Map<number, number>();
  for (const item of trainings) {
    if (item.profissional !== undefined) countByTrainer.set(item.profissional, (countByTrainer.get(item.profissional) ?? 0) + 1);
  }

  return (
    <section className="content-panel" aria-labelledby="team-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">EQUIPE ESPORTIVA</p><h2 id="team-title">Treinadores e treinos</h2><p className="muted">Consulte os treinadores e seus treinos agendados.</p></div>
        <span className="date-chip">♙ Equipe</span>
      </div>
      <form className="filter-bar" onSubmit={(event) => void load(event)}>
        <div className="filter-field"><label htmlFor="team-start">De</label><input id="team-start" type="date" required value={inicio} onChange={(event) => setInicio(event.target.value)} /></div>
        <div className="filter-field"><label htmlFor="team-end">Até</label><input id="team-end" type="date" required value={fim} onChange={(event) => setFim(event.target.value)} /></div>
        <button className="button button-primary" type="submit" disabled={loading}>Consultar <span aria-hidden="true">→</span></button>
      </form>
      <Message notice={message} />
      {loading && <Loading text="Carregando treinadores e agenda…" />}
      {!loading && !message?.kind.includes('error') && <>
        <div className="team-stats">
          <article><span>Treinadores cadastrados</span><strong>{trainers.length}</strong></article>
          <article><span>Treinos agendados no período</span><strong>{trainings.length}</strong></article>
        </div>
        <div className="agenda-heading"><div><h3>Equipe de treinamento</h3><p className="muted">Os cartões mostram quantos treinos cada profissional acompanhará.</p></div></div>
        {trainers.length === 0 ? <div className="empty-state"><h3>Nenhum treinador cadastrado</h3><p>Cadastre um profissional com perfil Treinador para exibi-lo aqui.</p></div> : <div className="team-cards">
          {trainers.map((trainer) => <article className="team-card" key={trainer.id}><span className="team-avatar" aria-hidden="true">{trainer.nome.slice(0, 1).toLocaleUpperCase('pt-BR')}</span><div className="team-person"><h4>{trainer.nome}</h4><p>{trainer.email || 'E-mail não informado'}</p></div><span className="team-session-count"><strong>{countByTrainer.get(trainer.id) ?? 0}</strong><small>treinos</small></span></article>)}
        </div>}
        <div className="agenda-heading"><div><h3>Treinos agendados</h3><p className="muted">Somente sessões futuras com situação Agendada e serviço da categoria Treino.</p></div><span className="muted">{trainings.length} item(ns)</span></div>
        {trainings.length === 0 ? <div className="empty-state"><h3>Nenhum treino agendado</h3><p>Não há treinos para o intervalo selecionado.</p></div> : <div className="team-schedule">{trainings.map((session) => {
          const trainer = trainersById.get(session.profissional ?? -1);
          const service = servicesById.get(session.servico ?? -1);
          return <article className="team-schedule-row" key={session.id}><div className="team-date"><strong>{formatDateTime(session.inicio)}</strong><small>até {formatDateTime(session.fim)}</small></div><div className="team-training"><h4>{session.titulo || 'Treino agendado'}</h4><p>{service?.nome ?? 'Serviço Treino'} · {session.participantes.length} participante(s)</p></div><div className="team-assignee"><span className="team-avatar small" aria-hidden="true">{trainer?.nome.slice(0, 1).toLocaleUpperCase('pt-BR')}</span><span><strong>{trainer?.nome}</strong><small>Treinador responsável</small></span></div><span className="tag status">Agendada</span></article>;
        })}</div>}
      </>}
    </section>
  );
}

/** Configura disponibilidade e bloqueios da equipe; as regras de conflito ficam na API. */
export function Disponibilidade({ onUnauthorized }: Props) {
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [availability, setAvailability] = useState<AgendaRange[]>([]);
  const [blocks, setBlocks] = useState<AgendaRange[]>([]);
  const [kind, setKind] = useState<'disponibilidade' | 'bloqueio'>('disponibilidade');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [people, availabilities, blockages] = await Promise.all([
        api<Professional[]>('/api/profissionais/'),
        api<AgendaRange[]>('/api/disponibilidades/'),
        api<AgendaRange[]>('/api/bloqueios-agenda/'),
      ]);
      setProfessionals(people);
      setAvailability(availabilities);
      setBlocks(blockages);
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setLoading(false);
    }
  }, [onUnauthorized]);

  useEffect(() => { void load(); }, [load]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const body: Omit<AgendaRange, 'id'> = {
      profissional: Number(values.get('profissional')),
      inicio: new Date(String(values.get('inicio'))).toISOString(),
      fim: new Date(String(values.get('fim'))).toISOString(),
    };
    if (kind === 'bloqueio') body.motivo = String(values.get('motivo') ?? '').trim();
    setBusy(true);
    setMessage(null);
    try {
      await api(kind === 'disponibilidade' ? '/api/disponibilidades/' : '/api/bloqueios-agenda/', { method: 'POST', body });
      form.reset();
      await load();
      setMessage({ kind: 'success', message: kind === 'disponibilidade' ? 'Disponibilidade cadastrada.' : 'Bloqueio cadastrado.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  async function remove(resource: 'disponibilidade' | 'bloqueio', id: number) {
    if (!window.confirm('Remover este período da agenda?')) return;
    setBusy(true);
    setMessage(null);
    try {
      await api(resource === 'disponibilidade' ? `/api/disponibilidades/${id}/` : `/api/bloqueios-agenda/${id}/`, { method: 'DELETE' });
      await load();
      setMessage({ kind: 'success', message: 'Período removido.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  const professionalsById = new Map(professionals.map((item) => [item.id, item.nome]));
  const rows = [
    ...availability.map((item) => ({ ...item, kind: 'disponibilidade' as const })),
    ...blocks.map((item) => ({ ...item, kind: 'bloqueio' as const })),
  ].sort((a, b) => a.inicio.localeCompare(b.inicio));

  return (
    <section className="content-panel" aria-labelledby="availability-title">
      <div className="panel-title-row"><div><p className="eyebrow">CONFIGURAÇÃO DA AGENDA</p><h2 id="availability-title">Disponibilidade</h2><p className="muted">Defina os períodos de atendimento e os bloqueios dos profissionais.</p></div><span className="date-chip">⚙ Agenda da equipe</span></div>
      <Message notice={message} />
      <div className="availability-layout">
        <form className="availability-form" onSubmit={(event) => void create(event)}>
          <div className="record-tabs" role="tablist" aria-label="Tipo de período">
            <button className={`record-tab${kind === 'disponibilidade' ? ' is-active' : ''}`} role="tab" aria-selected={kind === 'disponibilidade'} type="button" onClick={() => setKind('disponibilidade')}>Disponibilidade</button>
            <button className={`record-tab${kind === 'bloqueio' ? ' is-active' : ''}`} role="tab" aria-selected={kind === 'bloqueio'} type="button" onClick={() => setKind('bloqueio')}>Bloqueio</button>
          </div>
          <div className="form-grid"><label htmlFor="range-professional">Profissional<select id="range-professional" name="profissional" required defaultValue=""><option value="" disabled>Selecione</option>{professionals.map((item) => <option value={item.id} key={item.id}>{item.nome}</option>)}</select></label><label htmlFor="range-start">Início<input id="range-start" name="inicio" type="datetime-local" required /></label><label htmlFor="range-end">Fim<input id="range-end" name="fim" type="datetime-local" required /></label>{kind === 'bloqueio' && <label htmlFor="range-reason">Motivo <span className="optional-label">opcional</span><input id="range-reason" name="motivo" maxLength={200} /></label>}</div>
          <button className="button button-primary" type="submit" disabled={busy || loading || professionals.length === 0}>{busy ? 'Salvando…' : 'Adicionar período'} <span aria-hidden="true">→</span></button>
          {!loading && professionals.length === 0 && <p className="muted">Cadastre um profissional antes de configurar a agenda.</p>}
        </form>
        <div className="range-list-area"><div className="agenda-heading"><h3>Períodos cadastrados</h3><button className="text-button" type="button" onClick={() => void load()} disabled={loading}>↻ Atualizar</button></div>
          {loading ? <Loading text="Carregando períodos…" /> : rows.length === 0 ? <div className="empty-state"><h3>Nenhum período cadastrado</h3><p>Adicione uma disponibilidade ou um bloqueio.</p></div> : <div className="range-list">{rows.map((item) => <article className="range-card" key={`${item.kind}-${item.id}`}><span className={`range-icon ${item.kind}`} aria-hidden="true">{item.kind === 'disponibilidade' ? '✓' : '⊘'}</span><div><div className="range-card-title"><strong>{professionalsById.get(item.profissional) ?? `Profissional #${item.profissional}`}</strong><span className={`tag ${item.kind === 'bloqueio' ? 'warning-tag' : ''}`}>{item.kind === 'disponibilidade' ? 'Disponível' : 'Bloqueado'}</span></div><p>{formatDateTime(item.inicio)} – {formatDateTime(item.fim)}</p>{item.motivo && <small>{item.motivo}</small>}</div><button className="icon-button remove-button" aria-label="Remover período" type="button" disabled={busy} onClick={() => void remove(item.kind, item.id)}>×</button></article>)}</div>}
        </div>
      </div>
    </section>
  );
}
