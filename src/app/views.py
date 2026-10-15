from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.models import Aluno, Professor, Sessao
from app.serializers import AlunoSerializer, ProfessorSerializer, SessaoSerializer


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer


class ProfessorViewSet(ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer


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
