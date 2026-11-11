from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from app.agendamento import (
    AgendaComSessaoConfirmada,
    RegraDeAgendamentoViolada,
    alterar_agenda,
    validar_bloqueio,
    validar_saida_de_disponibilidade,
)
from app.models import Aluno, BloqueioAgenda, Disponibilidade, Servico, Sessao, Usuario
from app.operacao import mes_atual, pendencias_operacionais, resumo_por_servico
from app.permissoes import (
    PodeAdministrarCadastros,
    PodeAlterarSessao,
    PodeConfirmarAgendamento,
    PodeRemoverSessao,
    SomenteAdministrador,
    perfil_da_conta,
)
from app.serializers import (
    AlunoSerializer,
    BloqueioAgendaSerializer,
    DisponibilidadeSerializer,
    FiltroAgendaQueryParamsSerializer,
    FiltroPendenciasQueryParamsSerializer,
    PeriodoDashboardQueryParamsSerializer,
    ProfissionalSerializer,
    RegistroPresencaSerializer,
    ServicoSerializer,
    SessaoSerializer,
)


class Conflito(APIException):
    """Recusa uma operação que deixaria outros registros inconsistentes."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A operação conflita com registros existentes.'
    default_code = 'conflito'


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # As participações protegem o aluno; sem esta checagem o delete virava erro 500.
        if instance.participacoes.exists():
            raise Conflito(
                'Este aluno participa de sessões. Remova-o das sessões antes de excluir o cadastro.'
            )
        instance.delete()


class ProfissionalViewSet(ModelViewSet):
    queryset = Usuario.objects.filter(perfil__in=Usuario.PERFIS_PROFISSIONAIS)
    serializer_class = ProfissionalSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # As sessões protegem o responsável; sem esta checagem o delete virava erro 500.
        if instance.sessoes.exists():
            raise Conflito(
                'Este profissional é responsável por sessões. Transfira as sessões para outro '
                'profissional antes de removê-lo.'
            )
        # Apagar a conta encerra o acesso à API e remove o cadastro em cascata.
        instance.conta.delete()


class ServicoViewSet(ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # As sessões protegem o serviço; sem esta checagem o delete virava erro 500.
        if instance.sessoes.exists():
            raise Conflito(
                'Este serviço possui sessões agendadas ou realizadas e não pode ser excluído.'
            )
        instance.delete()


class SessaoViewSet(ModelViewSet):
    queryset = Sessao.objects.prefetch_related('participacoes')
    serializer_class = SessaoSerializer

    # Campos que o profissional responsável pode mudar: se a sessão foi ministrada (RF-10) e observações.
    CAMPOS_DO_RESPONSAVEL = {'status', 'observacoes'}

    def get_queryset(self):
        """Aplica o escopo da agenda e os filtros permitidos para cada perfil."""
        queryset = self.queryset.all().select_related('profissional', 'servico')
        usuario = getattr(self.request.user, 'usuario', None)
        if usuario is not None and usuario.perfil == Usuario.Perfil.PROFISSIONAL_SAUDE:
            queryset = queryset.filter(
                profissional=usuario,
                servico__categoria__in=[
                    Servico.Categoria.FISIOTERAPIA,
                    Servico.Categoria.PSICOLOGIA,
                    Servico.Categoria.NUTRICAO,
                ],
                servico__vinculos__profissional=usuario,
            )
        elif usuario is not None and usuario.perfil == Usuario.Perfil.TREINADOR:
            queryset = queryset.filter(profissional=usuario)

        if self.action in ('list', 'pendentes_status'):
            periodo = FiltroAgendaQueryParamsSerializer(data=self.request.query_params)
            periodo.is_valid(raise_exception=True)
            if 'inicio' in periodo.validated_data:
                queryset = queryset.filter(fim__gt=periodo.validated_data['inicio'])
            if 'fim' in periodo.validated_data:
                queryset = queryset.filter(inicio__lt=periodo.validated_data['fim'])
            if 'servico' in periodo.validated_data:
                servico = periodo.validated_data['servico']
                if (
                    usuario is not None
                    and usuario.perfil in (
                        Usuario.Perfil.TREINADOR,
                        Usuario.Perfil.PROFISSIONAL_SAUDE,
                    )
                    and not usuario.vinculos.filter(servico=servico).exists()
                ):
                    raise PermissionDenied('Só é possível filtrar por serviços vinculados ao seu perfil.')
                queryset = queryset.filter(servico=servico)

        return queryset.order_by('inicio', 'pk')

    def get_permissions(self):
        # Confirmar agendamento é do Administrador (UC-05), assim como remover sessões.
        if self.action == 'create':
            return [PodeConfirmarAgendamento()]
        if self.action == 'destroy':
            return [PodeRemoverSessao()]
        if self.action in ('update', 'partial_update'):
            return [PodeAlterarSessao()]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            serializer.save()
        except RegraDeAgendamentoViolada as erro:
            raise Conflito({'regra': erro.regra, 'detail': erro.mensagem}) from erro

    def perform_update(self, serializer):
        if perfil_da_conta(self.request.user) != Usuario.Perfil.ADMINISTRADOR:
            sessao = serializer.instance
            alterados = {
                campo for campo, valor in serializer.validated_data.items()
                if getattr(sessao, campo) != valor
            }
            if alterados - self.CAMPOS_DO_RESPONSAVEL:
                raise PermissionDenied(
                    'O profissional responsável altera apenas a situação e as observações da sessão.'
                )
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='presencas')
    def presencas(self, request, pk=None):
        """Registra presença ou falta dos participantes (RF-06), só pelo responsável (RN-05)."""
        sessao = self.get_object()
        usuario = getattr(request.user, 'usuario', None)
        if usuario is None or sessao.profissional_id != usuario.pk:
            raise PermissionDenied('Apenas o profissional responsável pela sessão registra presença ou falta.')
        if sessao.status == Sessao.Status.CANCELADA:
            raise Conflito('Sessão cancelada não recebe registro de presença ou falta.')

        entrada = RegistroPresencaSerializer(data=request.data, context={'sessao': sessao})
        entrada.is_valid(raise_exception=True)
        with transaction.atomic():
            participacoes = {
                participacao.aluno_id: participacao
                for participacao in sessao.participacoes.select_for_update()
            }
            for item in entrada.validated_data['presencas']:
                participacao = participacoes[item['aluno']]
                participacao.situacao_presenca = item['situacao']
                participacao.save()

        sessao = self.get_queryset().get(pk=sessao.pk)
        return Response(self.get_serializer(sessao).data)

    @action(detail=False, methods=['get'], url_path='pendentes-status')
    def pendentes_status(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.get_queryset().filter(
            status=Sessao.Status.AGENDADA,
            fim__lte=limite,
        )
        serializer = self.get_serializer(sessoes, many=True)
        return Response(serializer.data)


def _conflito_de_agenda(erro):
    conflito = Conflito()
    # Atribuído depois do construtor, que converteria o ID da sessão em texto.
    conflito.detail = {'regra': erro.regra, 'detail': erro.mensagem, 'sessao': erro.sessao.pk}
    return conflito


def _faixa_resultante(serializer):
    """Profissional e intervalo que a faixa terá depois de gravada (POST, PUT ou PATCH)."""
    atual = serializer.instance
    dados = serializer.validated_data
    return {
        campo: dados.get(campo, getattr(atual, campo, None))
        for campo in ('profissional', 'inicio', 'fim')
    }


class DisponibilidadeViewSet(ModelViewSet):
    """Gerencia períodos de disponibilidade com leitura autenticada e escrita administrativa.

    Remover ou reduzir uma disponibilidade que cobre sessão confirmada responde 409 (D-18).
    """

    queryset = Disponibilidade.objects.select_related('profissional').all()
    serializer_class = DisponibilidadeSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_update(self, serializer):
        atual = serializer.instance
        nova = _faixa_resultante(serializer)
        try:
            alterar_agenda(
                [atual.profissional, nova['profissional']],
                lambda: validar_saida_de_disponibilidade(atual, nova),
                serializer.save,
            )
        except AgendaComSessaoConfirmada as erro:
            raise _conflito_de_agenda(erro) from erro

    def perform_destroy(self, instance):
        try:
            alterar_agenda(
                [instance.profissional],
                lambda: validar_saida_de_disponibilidade(instance),
                instance.delete,
            )
        except AgendaComSessaoConfirmada as erro:
            raise _conflito_de_agenda(erro) from erro


class BloqueioAgendaViewSet(ModelViewSet):
    """Gerencia bloqueios com leitura autenticada e escrita administrativa.

    Bloqueio sobre sessão confirmada responde 409 (D-18).
    """

    queryset = BloqueioAgenda.objects.select_related('profissional').all()
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [PodeAdministrarCadastros]

    def _gravar(self, serializer):
        faixa = _faixa_resultante(serializer)
        try:
            alterar_agenda(
                [faixa['profissional']],
                lambda: validar_bloqueio(**faixa),
                serializer.save,
            )
        except AgendaComSessaoConfirmada as erro:
            raise _conflito_de_agenda(erro) from erro

    def perform_create(self, serializer):
        self._gravar(serializer)

    def perform_update(self, serializer):
        self._gravar(serializer)


class DashboardView(APIView):
    """Dashboard simples da operação, exclusivo do Administrador (RF-11)."""

    permission_classes = [SomenteAdministrador]

    def get(self, request):
        periodo = PeriodoDashboardQueryParamsSerializer(data=request.query_params)
        periodo.is_valid(raise_exception=True)
        inicio, fim = mes_atual()
        inicio = periodo.validated_data.get('inicio', inicio)
        fim = periodo.validated_data.get('fim', fim)
        return Response(resumo_por_servico(inicio, fim))


class PendenciasView(APIView):
    """Pendências operacionais da agenda, exclusivas do Administrador (RF-09).

    É só consulta: o atalho `detalhe` abre a sessão, mas presença e relatório continuam
    sendo alterados apenas pelo profissional responsável (RN-05).
    """

    permission_classes = [SomenteAdministrador]

    def get(self, request):
        filtro = FiltroPendenciasQueryParamsSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        return Response(pendencias_operacionais(tipo=filtro.validated_data.get('tipo')))
