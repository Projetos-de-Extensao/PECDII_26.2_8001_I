from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.agendamento import RegraDeAgendamentoViolada
from app.models import Aluno, BloqueioAgenda, Disponibilidade, RelatorioTreino, Servico, Sessao, Usuario
from app.permissoes import (
    PodeAdministrarCadastros,
    PodeAlterarSessao,
    PodeConfirmarAgendamento,
    PodeRemoverSessao,
    perfil_da_conta,
)
from app.serializers import (
    AlunoSerializer,
    BloqueioAgendaSerializer,
    DisponibilidadeSerializer,
    FiltroAgendaQueryParamsSerializer,
    ProfissionalSerializer,
    RelatorioTreinoSerializer,
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
    MENSAGEM_SESSAO_NAO_ENCERRADA = 'A presença e a situação da sessão só podem ser registradas a partir do fim previsto.'

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
        sessao = serializer.instance
        novo_status = serializer.validated_data.get('status', sessao.status)
        if (
            novo_status in (Sessao.Status.REALIZADA, Sessao.Status.NAO_REALIZADA)
            and novo_status != sessao.status
            and timezone.now() < sessao.fim
        ):
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)
        if perfil_da_conta(self.request.user) != Usuario.Perfil.ADMINISTRADOR:
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
        if timezone.now() < sessao.fim:
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)

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

    def _exigir_responsavel_treinador(self, sessao):
        usuario = getattr(self.request.user, 'usuario', None)
        if (
            usuario is None
            or usuario.perfil != Usuario.Perfil.TREINADOR
            or sessao.profissional_id != usuario.pk
        ):
            raise PermissionDenied('Somente o Treinador responsável pode criar ou alterar o relatório de treino.')

    def _validar_sessao_para_relatorio(self, sessao):
        if sessao.servico_id is None or sessao.servico.categoria != Servico.Categoria.TREINO:
            raise Conflito('O relatório de treino só pode ser associado a uma sessão do serviço Treino.')
        if sessao.status != Sessao.Status.REALIZADA:
            raise Conflito('A sessão precisa estar marcada como realizada antes de registrar o relatório.')
        if timezone.now() < sessao.fim:
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)

    @action(detail=True, methods=['get', 'post', 'patch'], url_path='relatorio')
    def relatorio(self, request, pk=None):
        """Consulta, cria ou edita o rascunho do relatório único da sessão de Treino."""
        sessao = self.get_object()
        perfil = perfil_da_conta(request.user)
        if request.method == 'GET':
            if perfil not in (Usuario.Perfil.ADMINISTRADOR, Usuario.Perfil.TREINADOR):
                raise PermissionDenied('Somente Administrador e Treinador podem consultar relatórios de treino.')
            if perfil == Usuario.Perfil.TREINADOR:
                self._exigir_responsavel_treinador(sessao)
            try:
                relatorio = sessao.relatorio_treino
            except RelatorioTreino.DoesNotExist as erro:
                raise NotFound('Esta sessão ainda não possui relatório de treino.') from erro
            return Response(RelatorioTreinoSerializer(relatorio).data)

        self._exigir_responsavel_treinador(sessao)
        self._validar_sessao_para_relatorio(sessao)
        with transaction.atomic():
            sessao = Sessao.objects.select_for_update().select_related('servico').get(pk=sessao.pk)
            if request.method == 'POST':
                if RelatorioTreino.objects.filter(sessao=sessao).exists():
                    raise Conflito('Esta sessão já possui um relatório de treino.')
                serializer = RelatorioTreinoSerializer(data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                try:
                    relatorio = serializer.save(sessao=sessao)
                except IntegrityError as erro:
                    raise Conflito('Esta sessão já possui um relatório de treino.') from erro
                return Response(RelatorioTreinoSerializer(relatorio).data, status=status.HTTP_201_CREATED)

            try:
                relatorio = RelatorioTreino.objects.select_for_update().get(sessao=sessao)
            except RelatorioTreino.DoesNotExist as erro:
                raise Conflito('Crie um rascunho antes de editar ou finalizar o relatório.') from erro
            if relatorio.status == RelatorioTreino.Status.FINALIZADO:
                raise Conflito('Relatórios finalizados são imutáveis.')
            serializer = RelatorioTreinoSerializer(relatorio, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            relatorio = serializer.save()
        return Response(RelatorioTreinoSerializer(relatorio).data)

    @action(detail=True, methods=['post'], url_path='relatorio/finalizar')
    def finalizar_relatorio(self, request, pk=None):
        """Valida todos os campos obrigatórios e finaliza o relatório em caráter imutável."""
        sessao = self.get_object()
        self._exigir_responsavel_treinador(sessao)
        self._validar_sessao_para_relatorio(sessao)
        with transaction.atomic():
            sessao = Sessao.objects.select_for_update().select_related('servico').get(pk=sessao.pk)
            try:
                relatorio = RelatorioTreino.objects.select_for_update().get(sessao=sessao)
            except RelatorioTreino.DoesNotExist as erro:
                raise Conflito('Crie um rascunho antes de finalizar o relatório.') from erro
            if relatorio.status == RelatorioTreino.Status.FINALIZADO:
                raise Conflito('Relatórios finalizados são imutáveis.')

            serializer = RelatorioTreinoSerializer(relatorio, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.validar_completo_para_finalizacao(serializer.validated_data)
            relatorio = serializer.save(
                status=RelatorioTreino.Status.FINALIZADO,
                finalizado_em=timezone.now(),
            )
        return Response(RelatorioTreinoSerializer(relatorio).data)

    @action(detail=False, methods=['get'], url_path='pendentes-status')
    def pendentes_status(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.get_queryset().filter(
            status=Sessao.Status.AGENDADA,
            fim__lte=limite,
        )
        serializer = self.get_serializer(sessoes, many=True)
        return Response(serializer.data)


class DisponibilidadeViewSet(ModelViewSet):
    """Gerencia períodos de disponibilidade com leitura autenticada e escrita administrativa."""

    queryset = Disponibilidade.objects.select_related('profissional').all()
    serializer_class = DisponibilidadeSerializer
    permission_classes = [PodeAdministrarCadastros]


class BloqueioAgendaViewSet(ModelViewSet):
    """Gerencia bloqueios com leitura autenticada e escrita administrativa."""

    queryset = BloqueioAgenda.objects.select_related('profissional').all()
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [PodeAdministrarCadastros]
