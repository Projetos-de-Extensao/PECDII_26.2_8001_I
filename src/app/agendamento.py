"""Confirmação de agendamento (UC-05): grava a sessão e os participantes numa única transação."""

from django.db import transaction

from app.models import Aluno, Participacao, Sessao, Usuario

# RN-02 / D-01: limite fixo para qualquer serviço, sem configuração administrativa no MVP.
CAPACIDADE_MAXIMA_SESSAO = 6


class RegraDeAgendamentoViolada(Exception):
    """Regra de negócio que depende do estado da agenda e impede a confirmação (409)."""

    def __init__(self, regra, mensagem):
        super().__init__(mensagem)
        self.regra = regra
        self.mensagem = mensagem


def validar_capacidade(alunos):
    """Recusa mais alunos do que a capacidade da sessão (RN-02)."""
    if len(alunos) > CAPACIDADE_MAXIMA_SESSAO:
        raise RegraDeAgendamentoViolada(
            'RN-02',
            f'Uma sessão pode ter no máximo {CAPACIDADE_MAXIMA_SESSAO} alunos; '
            f'foram informados {len(alunos)}.',
        )


def validar_regras_da_agenda(dados, alunos):
    """Valida as regras que dependem do que já está gravado na agenda.

    Roda dentro da transação, depois do bloqueio, para que duas confirmações simultâneas
    não passem pela validação com a mesma agenda (RN-06, RNF-03). As regras da #97
    (RN-03 disponibilidade e bloqueios, RN-04 habilitação) e da #98 (RN-01 e RN-07,
    conflitos) entram aqui e devem levantar RegraDeAgendamentoViolada.
    """
    validar_capacidade(alunos)


def _bloquear_recursos(profissional, alunos):
    """Trava o profissional e os alunos até o fim da transação.

    No PostgreSQL o select_for_update trava as linhas. No SQLite ele é ignorado; quem
    serializa as confirmações é o transaction_mode IMMEDIATE configurado em settings,
    que reserva a escrita do banco no início de cada transação.
    """
    list(Usuario.objects.select_for_update().filter(pk=profissional.pk))
    list(Aluno.objects.select_for_update().filter(pk__in=[aluno.pk for aluno in alunos]))


def confirmar_sessao(dados, alunos):
    """Confirma a sessão com seus participantes, por inteiro ou nada (RF-05, RN-06)."""
    with transaction.atomic():
        _bloquear_recursos(dados['profissional'], alunos)
        validar_regras_da_agenda(dados, alunos)
        sessao = Sessao.objects.create(**dados)
        for aluno in alunos:
            Participacao.objects.create(sessao=sessao, aluno=aluno)
    return sessao
