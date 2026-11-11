import { ApiError } from './api';
import type { Notice } from './types';

/** Traduz a resposta da API numa mensagem para a tela. As regras continuam no backend. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400: return `Revise os dados: ${error.message}`;
      case 401: return 'Sua sessão expirou. Entre novamente.';
      case 403: return `Acesso negado: ${error.message}`;
      case 404: return `Não encontrado: ${error.message}`;
      case 409: return `Operação recusada: ${error.message}`;
      default: return error.message;
    }
  }
  if (error instanceof TypeError) return 'Falha de conexão. Verifique a rede e tente novamente.';
  return 'Não foi possível concluir a solicitação.';
}

/** Volta ao login em 401; nos demais erros, mostra a mensagem. */
export function reportError(
  error: unknown,
  onUnauthorized: () => void,
  setMessage: (notice: Notice) => void,
): void {
  if (error instanceof ApiError && error.status === 401) {
    onUnauthorized();
    return;
  }
  setMessage({ kind: 'error', message: errorMessage(error) });
}

/** Monta "1 sessão" / "2 sessões" sem concatenar sufixos. */
export function plural(count: number, singular: string, pluralForm: string): string {
  return `${count} ${count === 1 ? singular : pluralForm}`;
}

/** Converte "2026-11-01" em "01/11/2026". */
export function formatDate(value: string): string {
  const [year, month, day] = value.split('-');
  return year && month && day ? `${day}/${month}/${year}` : value;
}

/** Mostra data e hora no padrão brasileiro. */
export function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date);
}
