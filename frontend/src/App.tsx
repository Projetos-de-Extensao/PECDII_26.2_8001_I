import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError, clearCsrf, refreshCsrf } from './api';
import { Dashboard, NovoAgendamento, Pendencias, VinculosProfissionais } from './AdminViews';
import { SessionActions } from './SessionActions';
import { Disponibilidade, EquipeTreinos } from './TeamViews';
import { errorMessage } from './errors';
import gaapLogo from './assets/gaap-logo.svg';
import type { Notice, Profile, RecordKind, Service, Session, SessionList, Student } from './types';

const profileLabels = {
  ADMINISTRADOR: 'Administrador',
  TREINADOR: 'Treinador',
  PROFISSIONAL_SAUDE: 'Profissional de Saúde',
} as const;

const categoryLabels: Record<string, string> = {
  TREINO: 'Treino',
  FISIOTERAPIA: 'Fisioterapia',
  PSICOLOGIA: 'Psicologia',
  NUTRICAO: 'Nutrição',
};

const statusLabels: Record<string, string> = {
  AGENDADA: 'Agendada',
  REALIZADA: 'Realizada',
  NAO_REALIZADA: 'Não realizada',
  CANCELADA: 'Cancelada',
};

function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return 'Falha de conexão. Verifique a rede e tente novamente.';
  if (error instanceof Error) return error.message;
  return 'Não foi possível concluir a solicitação.';
}

function localDateString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function currentWeek(): { start: string; end: string } {
  const today = new Date();
  const mondayOffset = (today.getDay() + 6) % 7;
  const monday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - mondayOffset);
  const sunday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6);
  return { start: localDateString(monday), end: localDateString(sunday) };
}

function localMidnightIso(value: string, nextDay = false): string {
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day + (nextDay ? 1 : 0));
  const offsetMinutes = -date.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? '+' : '-';
  const hours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(2, '0');
  const minutes = String(Math.abs(offsetMinutes) % 60).padStart(2, '0');
  return `${localDateString(date)}T00:00:00${sign}${hours}:${minutes}`;
}

function dateTime(value: string): { date: string; time: string } {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { date: 'Data não informada', time: '' };
  return {
    date: new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium' }).format(date),
    time: new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(date),
  };
}

function sessionsFrom(payload: Session[] | SessionList): Session[] {
  if (Array.isArray(payload)) return payload;
  return Array.isArray(payload.results) ? payload.results : [];
}

function NoticeBanner({ notice, onClose }: { notice: Notice | null; onClose?: () => void }) {
  if (!notice) return null;
  return (
    <div className={`notice notice-${notice.kind}`} role="status" aria-live="polite">
      <span>{notice.message}</span>
      {onClose && <button className="icon-button" type="button" aria-label="Fechar aviso" onClick={onClose}>×</button>}
    </div>
  );
}

function Login({ onLogin, notice }: { onLogin: (login: string, password: string) => Promise<void>; notice: Notice | null }) {
  const [loginName, setLoginName] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      await onLogin(loginName.trim(), password);
      setLoginName('');
      setPassword('');
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 401
        ? 'Login/e-mail ou senha incorretos.'
        : describeError(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <NoticeBanner notice={notice} />
      <main className="login-layout">
        <section className="welcome-panel" aria-labelledby="welcome-title">
          <p className="eyebrow">CENTRO DE ATENDIMENTO</p>
          <h1 id="welcome-title">Organize o cuidado.<br /><span>Acompanhe cada encontro.</span></h1>
          <p>Acesse a agenda e os cadastros do GAAP em um só lugar.</p>
          <div className="welcome-note"><span className="accent-dot" aria-hidden="true">✦</span> Um espaço de trabalho para a equipe e a comunidade.</div>
        </section>
        <section className="login-card" aria-labelledby="login-title">
          <div className="section-heading">
            <span className="section-icon" aria-hidden="true">↗</span>
            <div><p className="eyebrow">BEM-VINDO DE VOLTA</p><h2 id="login-title">Entrar na sua conta</h2></div>
          </div>
          <p className="muted">Use seu login ou e-mail para continuar.</p>
          <form onSubmit={submit}>
            <label htmlFor="login-name">Login ou e-mail</label>
            <input id="login-name" name="login" autoComplete="username" maxLength={150} required value={loginName} onChange={(event) => setLoginName(event.target.value)} placeholder="Digite seu login" />
            <label htmlFor="login-password">Senha</label>
            <input id="login-password" name="senha" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Digite sua senha" />
            {error && <p className="form-message error-text" role="alert">{error}</p>}
            <button className="button button-primary button-wide" type="submit" disabled={busy}>
              <span>{busy ? 'Entrando…' : 'Entrar'}</span><span aria-hidden="true">→</span>
            </button>
          </form>
          <p className="login-footnote">Precisa de acesso? Fale com o administrador do sistema.</p>
        </section>
      </main>
    </>
  );
}

function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [starting, setStarting] = useState(true);
  const [notice, setNotice] = useState<Notice | null>(null);
  const secureConnection = window.location.protocol === 'https:';

  useEffect(() => {
    let active = true;
    api<Profile>('/api/auth/session/')
      .then((user) => { if (active) setProfile(user); })
      .catch((error: unknown) => {
        if (!active) return;
        if (!(error instanceof ApiError && error.status === 401)) {
          setNotice({ message: 'Não foi possível consultar sua sessão. Verifique se a API está ativa.', kind: 'error' });
        }
      })
      .finally(() => { if (active) setStarting(false); });
    return () => { active = false; };
  }, []);

  const login = useCallback(async (loginName: string, password: string) => {
    setNotice(null);
    await refreshCsrf();
    await api('/api/auth/login/', { method: 'POST', body: { login: loginName, senha: password } });
    clearCsrf();
    await refreshCsrf();
    const user = await api<Profile>('/api/auth/session/');
    setProfile(user);
  }, []);

  const expireSession = useCallback(() => {
    clearCsrf();
    setProfile(null);
    setNotice({ message: 'Sua sessão expirou. Entre novamente.', kind: 'error' });
  }, []);

  const logout = useCallback(async () => {
    try {
      await api('/api/auth/logout/', { method: 'POST', body: {} });
      clearCsrf();
      setProfile(null);
      setNotice({ message: 'Você saiu da sua conta.', kind: 'success' });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        clearCsrf();
        setProfile(null);
        setNotice({ message: 'Sua sessão já estava encerrada.', kind: 'info' });
        return;
      }
      setNotice({ message: `Não foi possível encerrar a sessão. ${describeError(error)}`, kind: 'error' });
    }
  }, []);

  if (starting) {
    return <div className="startup-state" role="status"><span className="spinner" /> Carregando sua sessão…</div>;
  }

  return (
    <div className="page-shell">
      <header className="brand-bar">
        <a className="brand" href="/" aria-label="GAAP, início">
          <span className="brand-logo-frame">
            <img className="brand-logo" src={gaapLogo} width="393" height="82" alt="GAAP — Gestão de Atletas" />
          </span>
        </a>
        <span className={`secure-label ${secureConnection ? 'is-secure' : 'is-insecure'}`}>
          <span aria-hidden="true">●</span>
          {secureConnection ? 'Conexão protegida' : 'Conexão sem HTTPS'}
        </span>
      </header>

      {profile
        ? <Workspace profile={profile} notice={notice} onDismissNotice={() => setNotice(null)} onLogout={() => void logout()} onUnauthorized={expireSession} />
        : <Login onLogin={login} notice={notice} />}

      <footer className="site-footer"><span>GAAP <span aria-hidden="true">·</span> Gestão de atletas</span><span>Plataforma de gestão</span></footer>
    </div>
  );
}

type View = 'agenda' | 'pendencias' | 'dashboard' | 'agendamento' | 'cadastros' | 'equipe' | 'disponibilidade' | 'habilitacoes';

const adminViews: { id: View; label: string; icon: string }[] = [
  { id: 'agenda', label: 'Agenda', icon: '▦' },
  { id: 'pendencias', label: 'Pendências', icon: '!' },
  { id: 'dashboard', label: 'Dashboard', icon: '▤' },
  { id: 'agendamento', label: 'Novo agendamento', icon: '◷' },
  { id: 'equipe', label: 'Equipe e treinos', icon: '♙' },
  { id: 'disponibilidade', label: 'Disponibilidade', icon: '⚙' },
  { id: 'habilitacoes', label: 'Habilitações', icon: '✓' },
  { id: 'cadastros', label: 'Cadastros', icon: '＋' },
];

const professionalViews: { id: View; label: string; icon: string }[] = [
  { id: 'agenda', label: 'Agenda', icon: '▦' },
];

function Workspace({
  profile,
  notice,
  onDismissNotice,
  onLogout,
  onUnauthorized,
}: {
  profile: Profile;
  notice: Notice | null;
  onDismissNotice: () => void;
  onLogout: () => void;
  onUnauthorized: () => void;
}) {
  const [view, setView] = useState<View>('agenda');
  const isAdmin = profile.perfil === 'ADMINISTRADOR';
  // A API recusa com 403 o que o perfil não pode acessar; o menu só evita mostrar o que não se aplica.
  const views = isAdmin ? adminViews : professionalViews;

  function navButton(item: { id: View; label: string; icon: string }) {
    return (
      <button key={item.id} className={`nav-link${view === item.id ? ' is-active' : ''}`} type="button" aria-current={view === item.id ? 'page' : undefined} onClick={() => setView(item.id)}>
        <span aria-hidden="true">{item.icon}</span> {item.label}
      </button>
    );
  }

  return (
    <main className="workspace">
      <header className="workspace-header">
        <div><p className="eyebrow">ÁREA DE TRABALHO</p><h1>Olá, {profile.nome}</h1></div>
        <div className="profile-block"><span className="profile-badge">{profileLabels[profile.perfil]}</span><button className="button button-quiet" type="button" onClick={onLogout}>Sair <span aria-hidden="true">↗</span></button></div>
      </header>
      <NoticeBanner notice={notice} onClose={onDismissNotice} />
      <div className="workspace-body">
        <nav className="main-nav" aria-label="Navegação principal">
          {views.map(navButton)}
          <div className="nav-user"><span className="nav-user-mark" aria-hidden="true">{profile.nome.slice(0, 1).toLocaleUpperCase('pt-BR')}</span><span><strong>{profile.nome}</strong><small>{profileLabels[profile.perfil]}</small></span></div>
        </nav>
        {view === 'agenda' && <Agenda profile={profile} onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'pendencias' && <Pendencias onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'dashboard' && <Dashboard onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'agendamento' && <NovoAgendamento onUnauthorized={onUnauthorized} onManageLinks={() => setView('habilitacoes')} />}
        {isAdmin && view === 'equipe' && <EquipeTreinos profile={profile} onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'disponibilidade' && <Disponibilidade onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'habilitacoes' && <VinculosProfissionais onUnauthorized={onUnauthorized} />}
        {isAdmin && view === 'cadastros' && <Records onUnauthorized={onUnauthorized} />}
      </div>
    </main>
  );
}

function Agenda({ profile, onUnauthorized }: { profile: Profile; onUnauthorized: () => void }) {
  const initialRange = useRef(currentWeek());
  const [start, setStart] = useState(initialRange.current.start);
  const [end, setEnd] = useState(initialRange.current.end);
  const [service, setService] = useState('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [count, setCount] = useState(0);
  const [openSession, setOpenSession] = useState<number | null>(null);
  const [studentNames, setStudentNames] = useState(new Map<number, string>());
  const requestId = useRef(0);
  const isProfessional = profile.perfil !== 'ADMINISTRADOR';

  // Nomes dos alunos para o registro de presença; se falhar, a tela mostra o ID.
  useEffect(() => {
    if (!isProfessional) return;
    api<Student[]>('/api/alunos/')
      .then((students) => setStudentNames(new Map(students.map((item) => [item.id, item.nome]))))
      .catch(() => undefined);
  }, [isProfessional]);

  function replaceSession(updated: Session) {
    setSessions((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  }

  const loadAgenda = useCallback(async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    setError('');
    if (!start || !end || end < start) {
      setError('Informe um intervalo válido. A data final precisa ser igual ou posterior à inicial.');
      setLoading(false);
      return;
    }
    const id = ++requestId.current;
    setLoading(true);
    try {
      const query = new URLSearchParams({
        inicio: localMidnightIso(start),
        fim: localMidnightIso(end, true),
      });
      if (service) query.set('servico', service);
      const result = await api<Session[] | SessionList>(`/api/sessoes/?${query.toString()}`);
      if (id !== requestId.current) return;
      const rows = sessionsFrom(result);
      setSessions(rows);
      setCount(rows.length);
    } catch (reason) {
      if (id !== requestId.current) return;
      if (reason instanceof ApiError && reason.status === 401) {
        onUnauthorized();
        return;
      }
      setError(errorMessage(reason));
      setSessions([]);
      setCount(0);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [start, end, service, onUnauthorized]);

  useEffect(() => { void loadAgenda(); }, []); // A primeira busca usa a semana atual.

  const todayLabel = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'medium' }).format(new Date());
  const serviceById = new Map(profile.servicos.map((item: Service) => [String(item.id), item]));

  return (
    <section className="content-panel" aria-labelledby="agenda-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">ACOMPANHAMENTO</p><h2 id="agenda-title">Agenda</h2><p className="muted">Consulte os compromissos do período selecionado.</p></div>
        <span className="date-chip"><span aria-hidden="true">◷</span> {todayLabel}</span>
      </div>
      <form className="filter-bar" onSubmit={(event) => void loadAgenda(event)}>
        <div className="filter-field"><label htmlFor="filter-start">De</label><input id="filter-start" name="inicio" type="date" required value={start} onChange={(event) => setStart(event.target.value)} /></div>
        <div className="filter-field"><label htmlFor="filter-end">Até</label><input id="filter-end" name="fim" type="date" required value={end} onChange={(event) => setEnd(event.target.value)} /></div>
        {profile.servicos.length > 0 && <div className="filter-field"><label htmlFor="filter-service">Serviço</label><select id="filter-service" name="servico" value={service} onChange={(event) => setService(event.target.value)}><option value="">Todos os serviços</option>{profile.servicos.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}</select></div>}
        <button className="button button-primary" type="submit" disabled={loading}>Buscar agenda <span aria-hidden="true">→</span></button>
      </form>
      {error && <div className="inline-message error-message" role="alert">{error}</div>}
      <div className="agenda-heading"><h3>Sessões</h3><span className="muted">{loading ? 'Atualizando…' : `${count} sessão${count === 1 ? '' : 'ões'}`}</span></div>
      {loading && <div className="loading-card" role="status"><span className="spinner" /> Carregando sessões…</div>}
      {!loading && !error && sessions.length === 0 && <div className="empty-state"><span aria-hidden="true">▦</span><h3>Nenhuma sessão neste período</h3><p>Escolha outro intervalo para consultar a agenda.</p></div>}
      {!loading && sessions.length > 0 && <div className="session-list" aria-live="polite">{sessions.map((session) => {
        const from = dateTime(session.inicio);
        const to = dateTime(session.fim);
        const sessionService = serviceById.get(String(session.servico));
        const isOpen = openSession === session.id;
        return (
          <article className="session-card" key={session.id}>
            <div className="session-time"><span className="session-date">{from.date}</span>{from.time}{to.time ? ` – ${to.time}` : ''}</div>
            <div className="session-summary"><h4>{session.titulo || 'Sessão'}</h4><p>{sessionService?.nome ?? 'Serviço não informado'} · {session.participantes?.length ?? 0} participante(s)</p></div>
            <div className="session-meta">
              {sessionService?.categoria && <span className="tag">{categoryLabels[sessionService.categoria] ?? sessionService.categoria}</span>}
              <span className="tag status">{statusLabels[session.status] ?? session.status}</span>
              {isProfessional && <button className="button button-quiet" type="button" aria-expanded={isOpen} onClick={() => setOpenSession(isOpen ? null : session.id)}>{isOpen ? 'Fechar' : 'Detalhes'}</button>}
            </div>
            {isOpen && <SessionActions session={session} profile={profile} isTraining={sessionService?.categoria === 'TREINO'} studentNames={studentNames} onChanged={replaceSession} onUnauthorized={onUnauthorized} />}
          </article>
        );
      })}</div>}
    </section>
  );
}

function Records({ onUnauthorized }: { onUnauthorized: () => void }) {
  const [record, setRecord] = useState<RecordKind>('aluno');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);
  const endpointByType: Record<RecordKind, string> = {
    aluno: '/api/alunos/',
    profissional: '/api/profissionais/',
    servico: '/api/servicos/',
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    setMessage(null);
    if (!form.reportValidity()) return;
    const values = Object.fromEntries(new FormData(form).entries());
    for (const [key, value] of Object.entries(values)) {
      if (typeof value === 'string') values[key] = value.trim();
    }
    setBusy(true);
    try {
      await api(endpointByType[record], { method: 'POST', body: values });
      form.reset();
      setMessage({ message: 'Cadastro salvo com sucesso.', kind: 'success' });
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) {
        onUnauthorized();
        return;
      }
      const messageText = reason instanceof ApiError && reason.status === 403
        ? `Acesso negado: ${reason.message}`
        : reason instanceof ApiError
          ? `Revise os dados: ${reason.message}`
          : describeError(reason);
      setMessage({ message: messageText, kind: 'error' });
    } finally {
      setBusy(false);
    }
  }

  const tabs: { id: RecordKind; label: string }[] = [
    { id: 'aluno', label: 'Aluno' },
    { id: 'profissional', label: 'Profissional' },
    { id: 'servico', label: 'Serviço' },
  ];

  return (
    <section className="content-panel" aria-labelledby="records-title">
      <div className="panel-title-row"><div><p className="eyebrow">ADMINISTRAÇÃO</p><h2 id="records-title">Cadastros</h2><p className="muted">Inicie um cadastro. Os dados são validados pela API.</p></div><span className="date-chip">＋ Administração</span></div>
      <div className="record-tabs" role="tablist" aria-label="Tipo de cadastro">
        {tabs.map((tab) => <button key={tab.id} className={`record-tab${record === tab.id ? ' is-active' : ''}`} type="button" role="tab" aria-selected={record === tab.id} onClick={() => { setRecord(tab.id); setMessage(null); }}>{tab.label}</button>)}
      </div>
      {message && <div className={`inline-message ${message.kind === 'error' ? 'error-message' : 'success-message'}`} role="status" aria-live="polite">{message.message}</div>}
      {record === 'aluno' && <form className="record-form" onSubmit={(event) => void submit(event)}>
        <div className="form-intro"><span className="section-icon" aria-hidden="true">♙</span><div><h3>Novo aluno</h3><p>Preencha os dados básicos do cadastro.</p></div></div>
        <div className="form-grid"><label htmlFor="student-name">Nome completo<input id="student-name" name="nome" required maxLength={150} autoComplete="name" /></label><label htmlFor="student-birth">Data de nascimento<input id="student-birth" name="data_nascimento" type="date" required /></label><label htmlFor="student-phone">Telefone <span className="optional-label">opcional</span><input id="student-phone" name="telefone" type="tel" maxLength={20} autoComplete="tel" /></label></div>
        <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar aluno'} <span aria-hidden="true">→</span></button>
      </form>}
      {record === 'profissional' && <form className="record-form" onSubmit={(event) => void submit(event)}>
        <div className="form-intro"><span className="section-icon" aria-hidden="true">♙</span><div><h3>Novo profissional</h3><p>Crie o cadastro e as credenciais de acesso.</p></div></div>
        <div className="form-grid"><label htmlFor="professional-name">Nome completo<input id="professional-name" name="nome" required maxLength={150} autoComplete="name" /></label><label htmlFor="professional-email">E-mail<input id="professional-email" name="email" type="email" required maxLength={254} autoComplete="email" /></label><label htmlFor="professional-phone">Telefone <span className="optional-label">opcional</span><input id="professional-phone" name="telefone" type="tel" maxLength={20} autoComplete="tel" /></label><label htmlFor="professional-profile">Perfil<select id="professional-profile" name="perfil" required defaultValue=""><option value="" disabled>Selecione</option><option value="TREINADOR">Treinador</option><option value="PROFISSIONAL_SAUDE">Profissional de Saúde</option></select></label><label htmlFor="professional-login">Login<input id="professional-login" name="login" required maxLength={150} autoComplete="off" /></label><label htmlFor="professional-password">Senha<input id="professional-password" name="senha" type="password" required autoComplete="new-password" /></label></div>
        <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar profissional'} <span aria-hidden="true">→</span></button>
      </form>}
      {record === 'servico' && <form className="record-form" onSubmit={(event) => void submit(event)}>
        <div className="form-intro"><span className="section-icon" aria-hidden="true">✦</span><div><h3>Novo serviço</h3><p>Adicione uma modalidade ao catálogo.</p></div></div>
        <div className="form-grid service-grid"><label htmlFor="service-name">Nome do serviço<input id="service-name" name="nome" required maxLength={100} placeholder="Ex.: Fisioterapia individual" /></label><label htmlFor="service-category">Categoria<select id="service-category" name="categoria" required defaultValue=""><option value="" disabled>Selecione</option><option value="TREINO">Treino</option><option value="FISIOTERAPIA">Fisioterapia</option><option value="PSICOLOGIA">Psicologia</option><option value="NUTRICAO">Nutrição</option></select></label></div>
        <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar serviço'} <span aria-hidden="true">→</span></button>
      </form>}
    </section>
  );
}

export default App;

