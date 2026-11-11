import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from './api';
import { Loading, Message } from './AdminViews';
import { formatDate, reportError } from './errors';
import type { Notice, RecordKind } from './types';

/** Linha genérica vinda da API (aluno, profissional ou serviço). */
type Row = { id: number; [campo: string]: string | number };

const PERFIS: Record<string, string> = { TREINADOR: 'Treinador', PROFISSIONAL_SAUDE: 'Profissional de Saúde' };
const CATEGORIAS: Record<string, string> = { TREINO: 'Treino', FISIOTERAPIA: 'Fisioterapia', PSICOLOGIA: 'Psicologia', NUTRICAO: 'Nutrição' };

const CONFIG: Record<RecordKind, { endpoint: string; nome: string; colunas: string[]; linha: (row: Row) => string[] }> = {
  aluno: {
    endpoint: '/api/alunos/',
    nome: 'aluno',
    colunas: ['Nome', 'Nascimento', 'Telefone'],
    linha: (row) => [String(row.nome), formatDate(String(row.data_nascimento)), String(row.telefone || '—')],
  },
  profissional: {
    endpoint: '/api/profissionais/',
    nome: 'profissional',
    colunas: ['Nome', 'E-mail', 'Perfil'],
    linha: (row) => [String(row.nome), String(row.email), PERFIS[String(row.perfil)] ?? String(row.perfil)],
  },
  servico: {
    endpoint: '/api/servicos/',
    nome: 'serviço',
    colunas: ['Nome', 'Categoria'],
    linha: (row) => [String(row.nome), CATEGORIAS[String(row.categoria)] ?? String(row.categoria)],
  },
};

const ABAS: { id: RecordKind; label: string }[] = [
  { id: 'aluno', label: 'Alunos' },
  { id: 'profissional', label: 'Profissionais' },
  { id: 'servico', label: 'Serviços' },
];

/** Cadastros do Administrador: criar, consultar, editar e remover (RF-02). As validações ficam na API. */
export function Records({ onUnauthorized }: { onUnauthorized: () => void }) {
  const [record, setRecord] = useState<RecordKind>('aluno');
  const [rows, setRows] = useState<Row[]>([]);
  const [editing, setEditing] = useState<Row | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Notice | null>(null);
  const config = CONFIG[record];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setRows(await api<Row[]>(CONFIG[record].endpoint));
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setLoading(false);
    }
  }, [record, onUnauthorized]);

  useEffect(() => { void load(); }, [load]);

  function trocarAba(aba: RecordKind) {
    setRecord(aba);
    setEditing(null);
    setMessage(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values: Record<string, string> = {};
    new FormData(form).forEach((value, key) => { values[key] = String(value).trim(); });
    // Na edição, login e senha em branco significam "manter como está".
    if (editing) {
      if (!values.login) delete values.login;
      if (!values.senha) delete values.senha;
    }
    setMessage(null);
    setBusy(true);
    try {
      if (editing) {
        await api(`${config.endpoint}${editing.id}/`, { method: 'PATCH', body: values });
      } else {
        await api(config.endpoint, { method: 'POST', body: values });
      }
      form.reset();
      setEditing(null);
      setMessage({ kind: 'success', message: editing ? 'Cadastro atualizado.' : 'Cadastro salvo com sucesso.' });
      await load();
    } catch (error) {
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  async function remove(row: Row) {
    if (!window.confirm(`Remover o cadastro de ${row.nome}?`)) return;
    setMessage(null);
    setBusy(true);
    try {
      await api(`${config.endpoint}${row.id}/`, { method: 'DELETE' });
      if (editing?.id === row.id) setEditing(null);
      setMessage({ kind: 'success', message: 'Cadastro removido.' });
      await load();
    } catch (error) {
      // 409: o cadastro está em uso (sessões, participações); a mensagem da API explica o motivo.
      reportError(error, onUnauthorized, setMessage);
    } finally {
      setBusy(false);
    }
  }

  const valor = (campo: string) => (editing ? String(editing[campo] ?? '') : '');

  return (
    <section className="content-panel" aria-labelledby="records-title">
      <div className="panel-title-row">
        <div><p className="eyebrow">ADMINISTRAÇÃO</p><h2 id="records-title">Cadastros</h2><p className="muted">Crie, consulte, edite e remova cadastros. Os dados são validados pela API.</p></div>
      </div>
      <div className="record-tabs" role="tablist" aria-label="Tipo de cadastro">
        {ABAS.map((aba) => <button key={aba.id} className={`record-tab${record === aba.id ? ' is-active' : ''}`} type="button" role="tab" aria-selected={record === aba.id} onClick={() => trocarAba(aba.id)}>{aba.label}</button>)}
      </div>
      <Message notice={message} />

      {/* key recria o formulário ao trocar de aba ou de item em edição, para limpar os valores. */}
      <form key={`${record}-${editing?.id ?? 'novo'}`} className="record-form" onSubmit={(event) => void submit(event)}>
        <div className="form-intro"><div><h3>{editing ? `Editar ${config.nome}` : `Novo ${config.nome}`}</h3>{editing && <p>Editando: {String(editing.nome)}</p>}</div></div>
        {record === 'aluno' && <div className="form-grid">
          <label htmlFor="student-name">Nome completo<input id="student-name" name="nome" required maxLength={150} defaultValue={valor('nome')} /></label>
          <label htmlFor="student-birth">Data de nascimento<input id="student-birth" name="data_nascimento" type="date" required defaultValue={valor('data_nascimento')} /></label>
          <label htmlFor="student-phone">Telefone <span className="optional-label">opcional</span><input id="student-phone" name="telefone" type="tel" maxLength={20} defaultValue={valor('telefone')} /></label>
        </div>}
        {record === 'profissional' && <div className="form-grid">
          <label htmlFor="professional-name">Nome completo<input id="professional-name" name="nome" required maxLength={150} defaultValue={valor('nome')} /></label>
          <label htmlFor="professional-email">E-mail<input id="professional-email" name="email" type="email" required maxLength={254} defaultValue={valor('email')} /></label>
          <label htmlFor="professional-phone">Telefone <span className="optional-label">opcional</span><input id="professional-phone" name="telefone" type="tel" maxLength={20} defaultValue={valor('telefone')} /></label>
          <label htmlFor="professional-profile">Perfil<select id="professional-profile" name="perfil" required defaultValue={valor('perfil')}><option value="" disabled>Selecione</option><option value="TREINADOR">Treinador</option><option value="PROFISSIONAL_SAUDE">Profissional de Saúde</option></select></label>
          <label htmlFor="professional-login">Login {editing && <span className="optional-label">em branco mantém</span>}<input id="professional-login" name="login" required={!editing} maxLength={150} autoComplete="off" /></label>
          <label htmlFor="professional-password">Senha {editing && <span className="optional-label">em branco mantém</span>}<input id="professional-password" name="senha" type="password" required={!editing} autoComplete="new-password" /></label>
        </div>}
        {record === 'servico' && <div className="form-grid service-grid">
          <label htmlFor="service-name">Nome do serviço<input id="service-name" name="nome" required maxLength={100} defaultValue={valor('nome')} placeholder="Ex.: Fisioterapia individual" /></label>
          <label htmlFor="service-category">Categoria<select id="service-category" name="categoria" required defaultValue={valor('categoria')}><option value="" disabled>Selecione</option><option value="TREINO">Treino</option><option value="FISIOTERAPIA">Fisioterapia</option><option value="PSICOLOGIA">Psicologia</option><option value="NUTRICAO">Nutrição</option></select></label>
        </div>}
        <div className="button-row">
          <button className="button button-primary" type="submit" disabled={busy}>{busy ? 'Salvando…' : editing ? 'Salvar alterações' : `Salvar ${config.nome}`}</button>
          {editing && <button className="button button-quiet" type="button" onClick={() => setEditing(null)}>Cancelar edição</button>}
        </div>
      </form>

      {loading ? <Loading text="Carregando cadastros…" /> : (
        <div className="table-scroll">
          <table className="data-table">
            <thead><tr>{config.colunas.map((coluna) => <th scope="col" key={coluna}>{coluna}</th>)}<th scope="col">Ações</th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  {config.linha(row).map((celula, indice) => indice === 0 ? <th scope="row" key={indice}>{celula}</th> : <td key={indice}>{celula}</td>)}
                  <td>
                    <button className="text-button" type="button" disabled={busy} onClick={() => setEditing(row)}>Editar</button>
                    <button className="text-button danger-text" type="button" disabled={busy} onClick={() => void remove(row)}>Remover</button>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={config.colunas.length + 1}>Nenhum cadastro ainda.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
