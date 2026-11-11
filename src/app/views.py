from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.agendamento import RegraDeAgendamentoViolada
from app.models import Aluno, BloqueioAgenda, Disponibilidade, Servico, Sessao, Usuario
from app.permissoes import PodeAdministrarCadastros, PodeConfirmarAgendamento
from app.serializers import (
    AlunoSerializer,
    BloqueioAgendaSerializer,
    DisponibilidadeSerializer,
    ProfissionalSerializer,
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

    def get_permissions(self):
        # Confirmar agendamento é do Administrador (UC-05); os demais métodos seguem como antes.
        if self.action == 'create':
            return [PodeConfirmarAgendamento()]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            serializer.save()
        except RegraDeAgendamentoViolada as erro:
            raise Conflito({'regra': erro.regra, 'detail': erro.mensagem}) from erro

    @action(detail=False, methods=['get'], url_path='pendentes-status')
    def pendentes_status(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.queryset.filter(
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
