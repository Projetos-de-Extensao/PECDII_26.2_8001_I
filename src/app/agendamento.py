"""Confirmação de agendamento (UC-05): grava a sessão e os participantes numa única transação."""

from django.db import transaction
from django.utils import timezone

from app.models import (
    Aluno,
    BloqueioAgenda,
    Disponibilidade,
    Participacao,
    ProfissionalServico,
    Sessao,
    Usuario,
)

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
    conflitos) são verificadas antes de qualquer gravação.
    """
    validar_capacidade(alunos)

    servico = dados.get('servico')
    profissional = dados.get('profissional')
    inicio = dados.get('inicio')
    fim = dados.get('fim')

    if profissional is None or profissional.perfil not in Usuario.PERFIS_PROFISSIONAIS:
        raise RegraDeAgendamentoViolada(
            'RN-04', 'O responsável precisa ser Treinador ou Profissional de Saúde.'
        )
    if servico is None or not ProfissionalServico.objects.filter(
        profissional=profissional,
        servico=servico,
    ).exists():
        raise RegraDeAgendamentoViolada(
            'RN-04', 'O profissional não está habilitado para atender este serviço.'
        )
    if inicio is None or fim is None or fim <= inicio:
        raise RegraDeAgendamentoViolada(
            'RN-03', 'O fim da sessão deve ser posterior ao início.'
        )
    if not Disponibilidade.objects.filter(
        profissional=profissional,
        inicio__lte=inicio,
        fim__gte=fim,
    ).exists():
        raise RegraDeAgendamentoViolada(
            'RN-03', 'O horário solicitado está fora da disponibilidade do profissional.'
        )
    if BloqueioAgenda.objects.filter(
        profissional=profissional,
        inicio__lt=fim,
        fim__gt=inicio,
    ).exists():
        raise RegraDeAgendamentoViolada(
            'RN-03', 'O horário solicitado está dentro de um bloqueio da agenda.'
        )

    sessoes_conflitantes = Sessao.objects.filter(
        profissional=profissional,
        inicio__lt=fim,
        fim__gt=inicio,
    ).exclude(status=Sessao.Status.CANCELADA)
    if sessoes_conflitantes.exists():
        raise RegraDeAgendamentoViolada(
            'RN-01', 'O profissional já possui um compromisso neste horário.'
        )

    participacoes_conflitantes = Participacao.objects.filter(
        aluno__in=alunos,
        sessao__inicio__lt=fim,
        sessao__fim__gt=inicio,
    ).exclude(sessao__status=Sessao.Status.CANCELADA)
    participacao = participacoes_conflitantes.select_related('aluno').first()
    if participacao is not None:
        raise RegraDeAgendamentoViolada(
            'RN-07',
            f'O aluno {participacao.aluno.nome} já possui um compromisso neste horário.',
        )


def _bloquear_recursos(profissional, alunos):
    """Trava o profissional e os alunos até o fim da transação.

    No PostgreSQL o select_for_update trava as linhas. No SQLite ele é ignorado; quem
    serializa as confirmações é o transaction_mode IMMEDIATE configurado em settings,
    que reserva a escrita do banco no início de cada transação.
    """
    list(Usuario.objects.select_for_update().filter(pk=profissional.pk).order_by('pk'))
    list(
        Aluno.objects.select_for_update()
        .filter(pk__in=[aluno.pk for aluno in alunos])
        .order_by('pk')
    )


def confirmar_sessao(dados, alunos):
    """Confirma a sessão com seus participantes, por inteiro ou nada (RF-05, RN-06)."""
    with transaction.atomic():
        _bloquear_recursos(dados['profissional'], alunos)
        validar_regras_da_agenda(dados, alunos)
        sessao = Sessao.objects.create(**dados)
        for aluno in alunos:
            Participacao.objects.create(sessao=sessao, aluno=aluno)
    return sessao


# Alterações da agenda depois da confirmação (#119, D-18). Contam as sessões não canceladas
# que ainda não terminaram: as passadas não travam a limpeza de disponibilidades antigas.
def _sessoes_ativas(profissional, agora=None):
    return (
        Sessao.objects.filter(profissional=profissional, fim__gt=agora or timezone.now())
        .exclude(status=Sessao.Status.CANCELADA)
        .order_by('inicio', 'pk')
    )


def _descrever(sessao):
    inicio = timezone.localtime(sessao.inicio).strftime('%d/%m/%Y %H:%M')
    return f'sessão {sessao.pk} ({sessao.titulo}, {inicio})'


class AgendaComSessaoConfirmada(RegraDeAgendamentoViolada):
    """A alteração da disponibilidade ou do bloqueio deixaria uma sessão confirmada fora da agenda."""

    def __init__(self, mensagem, sessao):
        super().__init__('RN-03', mensagem)
        self.sessao = sessao


def validar_bloqueio(profissional, inicio, fim, agora=None):
    """Recusa o bloqueio que se sobrepõe a uma sessão confirmada do profissional (RN-03, D-18)."""
    sessao = _sessoes_ativas(profissional, agora).filter(inicio__lt=fim, fim__gt=inicio).first()
    if sessao is not None:
        raise AgendaComSessaoConfirmada(
            f'O bloqueio se sobrepõe à {_descrever(sessao)}, já confirmada. '
            'Cancele ou remaneje a sessão antes de bloquear o horário.',
            sessao,
        )


def validar_saida_de_disponibilidade(disponibilidade, nova=None, agora=None):
    """Recusa remover ou alterar a disponibilidade se uma sessão confirmada perder a cobertura.

    `disponibilidade` é o registro como está gravado; `nova`, quando houver, traz os valores
    que vão substituí-lo (`profissional`, `inicio`, `fim`). Só importam as sessões que estavam
    dentro dela, e cada uma continua coberta se outra disponibilidade do profissional, ou a
    própria versão nova, ainda abranger o horário inteiro (RN-03, D-18).
    """
    afetadas = _sessoes_ativas(disponibilidade.profissional, agora).filter(
        inicio__gte=disponibilidade.inicio,
        fim__lte=disponibilidade.fim,
    )
    outras = Disponibilidade.objects.filter(
        profissional=disponibilidade.profissional
    ).exclude(pk=disponibilidade.pk)
    for sessao in afetadas:
        if nova is not None and (
            nova['profissional'] == disponibilidade.profissional
            and nova['inicio'] <= sessao.inicio
            and nova['fim'] >= sessao.fim
        ):
            continue
        if outras.filter(inicio__lte=sessao.inicio, fim__gte=sessao.fim).exists():
            continue
        raise AgendaComSessaoConfirmada(
            f'A {_descrever(sessao)}, já confirmada, ficaria fora da disponibilidade do '
            'profissional. Cancele ou remaneje a sessão antes de alterar a disponibilidade.',
            sessao,
        )


def alterar_agenda(profissionais, validar, gravar):
    """Valida e grava uma alteração da agenda numa transação, como a confirmação.

    Trava os profissionais envolvidos, como `confirmar_sessao`, para que uma confirmação
    simultânea não valide contra a agenda antiga (RNF-03).
    """
    with transaction.atomic():
        list(
            Usuario.objects.select_for_update()
            .filter(pk__in={profissional.pk for profissional in profissionais})
            .order_by('pk')
        )
        validar()
        return gravar()
