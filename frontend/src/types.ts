export type ProfileName = 'ADMINISTRADOR' | 'TREINADOR' | 'PROFISSIONAL_SAUDE';

export interface Service {
  id: number;
  nome: string;
  categoria: string;
  profissionais_habilitados?: number[];
}

export interface ProfessionalServiceLink {
  id: number;
  profissional: number;
  servico: number;
}

export interface Profile {
  id: number;
  nome: string;
  email: string;
  perfil: ProfileName;
  servicos: Service[];
}

export type PresenceStatus = 'PRESENTE' | 'FALTA';

export interface Presence {
  aluno: number;
  situacao_presenca: PresenceStatus | null;
}

export interface Session {
  id: number;
  titulo: string;
  inicio: string;
  fim: string;
  servico: number | null;
  profissional?: number;
  participantes: number[];
  presencas?: Presence[];
  status: string;
}

export interface SessionList {
  results?: Session[];
}

export type RecordKind = 'aluno' | 'profissional' | 'servico';

export interface Student {
  id: number;
  nome: string;
}

export interface Professional {
  id: number;
  nome: string;
  email?: string;
  perfil: ProfileName;
}

export interface AgendaRange {
  id: number;
  profissional: number;
  inicio: string;
  fim: string;
  motivo?: string;
}

export interface Report {
  id: number;
  sessao: number;
  status: 'RASCUNHO' | 'FINALIZADO';
  data: string | null;
  horario: string | null;
  local: string;
  objetivo: string;
  exercicios: string;
  volume_valor: string | null;
  volume_unidade: string;
  intensidade_borg: string | null;
  finalizado_em: string | null;
}

export interface PendingItem {
  tipo: string;
  motivo: string;
  sessao: { id: number; titulo: string; inicio: string; fim: string; status: string; servico: Service };
  responsavel: { id: number; nome: string };
}

export interface PendingList {
  total: number;
  tipos: { valor: string; rotulo: string }[];
  itens: PendingItem[];
}

export interface DashboardRow {
  id: number;
  nome: string;
  por_situacao: Record<string, number>;
  total: number;
}

export interface DashboardData {
  periodo: { inicio: string; fim: string };
  situacoes: { valor: string; rotulo: string }[];
  servicos: DashboardRow[];
  total: { por_situacao: Record<string, number>; total: number };
}

export type NoticeKind = 'info' | 'success' | 'error';

export interface Notice {
  message: string;
  kind: NoticeKind;
}
