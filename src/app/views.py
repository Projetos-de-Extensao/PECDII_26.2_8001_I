from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.models import Aluno, Professor, Servico, Sessao, Usuario
from app.permissoes import PodeAdministrarCadastros
from app.serializers import (
    AlunoSerializer,
    ProfessorSerializer,
    ProfissionalSerializer,
    ServicoSerializer,
    SessaoSerializer,
)


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    permission_classes = [PodeAdministrarCadastros]


class ProfessorViewSet(ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [PodeAdministrarCadastros]


class ProfissionalViewSet(ModelViewSet):
    queryset = Usuario.objects.filter(perfil__in=Usuario.PERFIS_PROFISSIONAIS)
    serializer_class = ProfissionalSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # Apagar a conta encerra o acesso à API e remove o cadastro em cascata.
        instance.conta.delete()


class ServicoViewSet(ModelViewSet):
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer
    permission_classes = [PodeAdministrarCadastros]


class SessaoViewSet(ModelViewSet):
    queryset = Sessao.objects.all()
    serializer_class = SessaoSerializer

    @action(detail=False, methods=['get'], url_path='pendentes-status')
    def pendentes_status(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.queryset.filter(
            status=Sessao.Status.AGENDADA,
            fim__lte=limite,
        )
        serializer = self.get_serializer(sessoes, many=True)
        return Response(serializer.data)
