export type ProfileName = 'ADMINISTRADOR' | 'TREINADOR' | 'PROFISSIONAL_SAUDE';

export interface Service {
  id: number;
  nome: string;
  categoria: string;
}

export interface Profile {
  id: number;
  nome: string;
  email: string;
  perfil: ProfileName;
  servicos: Service[];
}

export interface Session {
  id: number;
  titulo: string;
  inicio: string;
  fim: string;
  servico: number | null;
  participantes: number[];
  status: string;
}

export interface SessionList {
  results?: Session[];
}

export type RecordKind = 'aluno' | 'profissional' | 'servico';

