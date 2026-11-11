import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { api, ApiError } from './api';
import { Message } from './AdminViews';
import { reportError } from './errors';
import type { Notice, PresenceStatus, Profile, Report, Session } from './types';

interface SessionActionsProps {
  session: Session;
  profile: Profile;
  isTraining: boolean;
  studentNames: Map<number, string>;
  onChanged: (session: Session) => void;
  onUnauthorized: () => void;
}

const REPORT_FIELDS = [
  { name: 'data', label: 'Data', type: 'date' },
  { name: 'horario', label: 'Horário', type: 'time' },
  { name: 'local', label: 'Local', type: 'text' },
  { name: 'objetivo', label: 'Objetivo', type: 'text' },
  { name: 'exercicios', label: 'Exercícios', type: 'text' },
  { name: 'volume_valor', label: 'Volume', type: 'number' },
  { name: 'volume_unidade', label: 'Unidade do volume', type: 'text' },
  { name: 'intensidade_borg', label: 'Intensidade (Borg 0–10)', type: 'number' },
] as const;

/**
 * Ações do profissional responsável sobre uma sessão.
 * Horário, permissão e estado da sessão são validados pela API; a tela só mostra a resposta.
 */
export function SessionActions({ session, profile, isTraining, studentNames, onChanged, onUnauthorized }: SessionActionsProps) {
  const isTrainer = profile.perfil === 'TREINADOR';
  return (
    <div className="session-actions">
      <PresenceForm session={session} studentNames={studentNames} onChanged={onChanged} onUnauthorized={onUnauthorized} />
      {isTrainer && <StatusButtons session={session} onChanged={onChanged} onUnauthorized={onUnauthorized} />}
      {isTrainer && isTraining && <ReportPanel session={session} onUnauthorized={onUnauthorized} />}
    </div>
  );
}

function PresenceForm({ session, studentNames, onChanged, onUnauthorized }: Omit<SessionActionsProps, 'profile' | 'isTraining'>) {
  const [message, setMessage] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);
  const current = new Map((session.presencas ?? []).map((item) => [item.aluno, item.situacao_presenca]));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const presencas = session.participantes
      .map((aluno) => ({ aluno, situacao: (form.get(`aluno-${aluno}`) ?? '') as PresenceStatus | '' }))
      .filter((item) => item.situacao !== '');
    setMessage(null);
    if (presencas.length === 0) {
      setMessage({ kind: 'error', message: 'Escolha presença ou falta para pelo menos um aluno.' });
      return;
    }
    setBusy(true);
    try {
      const updated = await api<Session>(`/api/sessoes/${session.id}/presencas/`, { method: 'PATCH', body: { presencas } });
      onChanged(updated);
      setMessage({ kind: 'success', message: 'Presença registrada.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="action-block" onSubmit={(event) => void submit(event)}>
      <h5>Presença</h5>
      {session.participantes.map((aluno) => (
        <label className="presence-row" key={aluno} htmlFor={`presence-${session.id}-${aluno}`}>
          <span>{studentNames.get(aluno) ?? `Aluno #${aluno}`}</span>
          <select id={`presence-${session.id}-${aluno}`} name={`aluno-${aluno}`} defaultValue={current.get(aluno) ?? ''}>
            <option value="">Não registrada</option>
            <option value="PRESENTE">Presente</option>
            <option value="FALTA">Falta</option>
          </select>
        </label>
      ))}
      <Message notice={message} />
      <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Salvando…' : 'Salvar presença'}</button>
    </form>
  );
}

function StatusButtons({ session, onChanged, onUnauthorized }: Pick<SessionActionsProps, 'session' | 'onChanged' | 'onUnauthorized'>) {
  const [message, setMessage] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);

  async function changeStatus(status: 'REALIZADA' | 'NAO_REALIZADA') {
    setMessage(null);
    setBusy(true);
    try {
      const updated = await api<Session>(`/api/sessoes/${session.id}/`, { method: 'PATCH', body: { status } });
      onChanged(updated);
      setMessage({ kind: 'success', message: 'Situação da sessão atualizada.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="action-block">
      <h5>A sessão foi realizada?</h5>
      <div className="button-row">
        <button className="button button-primary" type="button" disabled={busy} onClick={() => void changeStatus('REALIZADA')}>Marcar realizada</button>
        <button className="button button-quiet" type="button" disabled={busy} onClick={() => void changeStatus('NAO_REALIZADA')}>Marcar não realizada</button>
      </div>
      <Message notice={message} />
    </div>
  );
}

function ReportPanel({ session, onUnauthorized }: Pick<SessionActionsProps, 'session' | 'onUnauthorized'>) {
  const url = `/api/sessoes/${session.id}/relatorio/`;
  const formRef = useRef<HTMLFormElement>(null);
  const [opened, setOpened] = useState(false);
  const [report, setReport] = useState<Report | null>(null);
  const [message, setMessage] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);

  async function open() {
    setMessage(null);
    setBusy(true);
    try {
      setReport(await api<Report>(url));
      setOpened(true);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        // 404 aqui é esperado: a sessão ainda não tem relatório.
        setReport(null);
        setOpened(true);
        setMessage({ kind: 'info', message: 'Esta sessão ainda não tem relatório. Preencha e salve o rascunho.' });
      } else {
        reportError(error, onUnauthorized, setMessage);
      }
    } finally {
      setBusy(false);
    }
  }

  /** Envia só os campos preenchidos; a API valida o resto. */
  function filledFields(): Record<string, string> {
    const values: Record<string, string> = {};
    new FormData(formRef.current!).forEach((value, key) => {
      if (typeof value === 'string' && value.trim()) values[key] = value.trim();
    });
    return values;
  }

  async function save(finalize: boolean) {
    setMessage(null);
    setBusy(true);
    try {
      const result = finalize
        ? await api<Report>(`${url}finalizar/`, { method: 'POST', body: filledFields() })
        : await api<Report>(url, { method: report ? 'PATCH' : 'POST', body: filledFields() });
      setReport(result);
      setMessage({ kind: 'success', message: finalize ? 'Relatório finalizado.' : 'Rascunho salvo.' });
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  if (!opened) {
    return (
      <div className="action-block">
        <h5>Relatório de treino</h5>
        <button className="button button-quiet" type="button" disabled={busy} onClick={() => void open()}>{busy ? 'Abrindo…' : 'Abrir relatório'}</button>
        <Message notice={message} />
      </div>
    );
  }

  if (report?.status === 'FINALIZADO') {
    return (
      <div className="action-block">
        <h5>Relatório de treino <span className="tag status">Finalizado</span></h5>
        <dl className="report-summary">
          {REPORT_FIELDS.map((field) => <div key={field.name}><dt>{field.label}</dt><dd>{report[field.name] ?? '—'}</dd></div>)}
        </dl>
        <Message notice={message} />
      </div>
    );
  }

  return (
    <form className="action-block" ref={formRef} onSubmit={(event) => event.preventDefault()}>
      <h5>Relatório de treino {report && <span className="tag status">Rascunho</span>}</h5>
      <div className="form-grid">
        {REPORT_FIELDS.map((field) => (
          <label key={field.name} htmlFor={`report-${session.id}-${field.name}`}>{field.label}
            <input
              id={`report-${session.id}-${field.name}`}
              name={field.name}
              type={field.type}
              step={field.type === 'number' ? '0.1' : undefined}
              defaultValue={report?.[field.name] ?? ''}
            />
          </label>
        ))}
      </div>
      <Message notice={message} />
      <div className="button-row">
        <button className="button button-quiet" type="button" disabled={busy} onClick={() => void save(false)}>Salvar rascunho</button>
        <button className="button button-primary" type="button" disabled={busy} onClick={() => void save(true)}>Finalizar relatório</button>
      </div>
    </form>
  );
}
