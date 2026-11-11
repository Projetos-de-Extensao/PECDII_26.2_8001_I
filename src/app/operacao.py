"""Consultas operacionais do Administrador: pendências da agenda (RF-09) e dashboard (RF-11)."""

from datetime import datetime, time, timedelta

from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from app.models import Servico, Sessao


def mes_atual():
    """Devolve o primeiro e o último dia do mês corrente, no fuso do projeto."""
    hoje = timezone.localdate()
    inicio = hoje.replace(day=1)
    proximo_mes = (inicio + timedelta(days=32)).replace(day=1)
    return inicio, proximo_mes - timedelta(days=1)


def _inicio_do_dia(dia):
    return timezone.make_aware(datetime.combine(dia, time.min))


def _zeros():
    return {situacao: 0 for situacao in Sessao.Status.values}


def resumo_por_servico(inicio, fim):
    """Conta os compromissos por serviço e situação no período (RF-11, D-12).

    O período vai do primeiro minuto de `inicio` ao último minuto de `fim`, no fuso do projeto,
    e cada sessão conta pelo dia em que começa. Todos os serviços do catálogo aparecem, com
    zero nas situações sem ocorrência, ordenados pelo total geral decrescente e depois pelo nome.
    """
    contagens = (
        Sessao.objects.filter(
            inicio__gte=_inicio_do_dia(inicio),
            inicio__lt=_inicio_do_dia(fim + timedelta(days=1)),
        )
        .values('servico_id', 'status')
        .annotate(quantidade=Count('pk'))
    )
    por_servico = {}
    for linha in contagens:
        por_servico.setdefault(linha['servico_id'], _zeros())[linha['status']] = linha['quantidade']

    servicos = []
    total_geral = _zeros()
    for servico in Servico.objects.all():
        por_situacao = por_servico.get(servico.pk, _zeros())
        for situacao, quantidade in por_situacao.items():
            total_geral[situacao] += quantidade
        servicos.append({
            'id': servico.pk,
            'nome': servico.nome,
            'categoria': servico.categoria,
            'por_situacao': por_situacao,
            'total': sum(por_situacao.values()),
        })
    servicos.sort(key=lambda linha: (-linha['total'], linha['nome']))

    return {
        'periodo': {'inicio': inicio.isoformat(), 'fim': fim.isoformat()},
        'situacoes': [
            {'valor': valor, 'rotulo': rotulo} for valor, rotulo in Sessao.Status.choices
        ],
        'servicos': servicos,
        'total': {'por_situacao': total_geral, 'total': sum(total_geral.values())},
    }


# RF-09 / D-11. O relatório de treino (#109) ainda não existe; quando existir, entra o tipo
# RELATORIO_PENDENTE para sessões de Treino sem relatório ou com relatório em rascunho.
PRESENCA_PENDENTE = 'PRESENCA_PENDENTE'
TIPOS_DE_PENDENCIA = {
    PRESENCA_PENDENTE: 'Presença pendente',
}


def _pendencias_de_presenca(agora):
    """Compromissos encerrados, não cancelados, com participante sem presença ou falta."""
    sessoes = (
        Sessao.objects.filter(fim__lte=agora)
        .exclude(status=Sessao.Status.CANCELADA)
        .annotate(
            participantes=Count('participacoes'),
            sem_registro=Count('participacoes', filter=Q(participacoes__situacao_presenca__isnull=True)),
        )
        .filter(sem_registro__gt=0)
        .select_related('servico', 'profissional')
        .order_by('fim', 'pk')
    )
    for sessao in sessoes:
        yield {
            'tipo': PRESENCA_PENDENTE,
            'motivo': (
                f'{sessao.sem_registro} de {sessao.participantes} participante(s) '
                'sem presença ou falta registrada.'
            ),
            'sessao': {
                'id': sessao.pk,
                'titulo': sessao.titulo,
                'inicio': timezone.localtime(sessao.inicio).isoformat(),
                'fim': timezone.localtime(sessao.fim).isoformat(),
                'status': sessao.status,
                'servico': {
                    'id': sessao.servico_id,
                    'nome': sessao.servico.nome,
                    'categoria': sessao.servico.categoria,
                },
            },
            'responsavel': {'id': sessao.profissional_id, 'nome': sessao.profissional.nome},
            'detalhe': reverse('sessao-detail', args=[sessao.pk]),
        }


def pendencias_operacionais(tipo=None, agora=None):
    """Lista as pendências da agenda com motivo e responsável (RF-09, D-11).

    O total e a contagem por tipo consideram todas as pendências, mesmo com o filtro, para
    que o menu mostre o total geral enquanto a lista mostra só o tipo escolhido.
    """
    agora = agora or timezone.now()
    todas = list(_pendencias_de_presenca(agora))
    por_tipo = {chave: 0 for chave in TIPOS_DE_PENDENCIA}
    for item in todas:
        por_tipo[item['tipo']] += 1
    return {
        'total': len(todas),
        'por_tipo': por_tipo,
        'tipos': [{'valor': valor, 'rotulo': rotulo} for valor, rotulo in TIPOS_DE_PENDENCIA.items()],
        'itens': [item for item in todas if tipo is None or item['tipo'] == tipo],
    }
