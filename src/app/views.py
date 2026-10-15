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

    @action(detail=False, methods=['get'], url_path='pendentes-confirmacao')
    def pendentes_confirmacao(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.queryset.filter(
            status=Sessao.Status.AGENDADA,
            confirmacao_realizacao=Sessao.Confirmacao.PENDENTE,
            fim__lte=limite,
        )
        serializer = self.get_serializer(sessoes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='confirmar-realizacao')
    def confirmar_realizacao(self, request, pk=None):
        """Confirma a realização da sessão e salva observações informadas."""
        sessao = self.get_object()
        ocorreu = request.data.get('ocorreu')
        observacoes = request.data.get('observacoes')
        if not isinstance(ocorreu, bool):
            return Response(
                {'ocorreu': 'Informe true ou false.'},
                status=400,
            )
        if observacoes is not None and not isinstance(observacoes, str):
            return Response(
                {'observacoes': 'Informe um texto.'},
                status=400,
            )
        if sessao.status != Sessao.Status.AGENDADA:
            return Response(
                {'detail': 'Somente sessões agendadas podem receber confirmação.'},
                status=400,
            )
        if timezone.now() < sessao.fim + timedelta(minutes=30):
            return Response(
                {'detail': 'A confirmação fica disponível 30 minutos após o término previsto.'},
                status=400,
            )
        if ocorreu:
            sessao.confirmacao_realizacao = Sessao.Confirmacao.OCORREU
            sessao.status = Sessao.Status.REALIZADA
        else:
            sessao.confirmacao_realizacao = Sessao.Confirmacao.NAO_OCORREU
            sessao.status = Sessao.Status.NAO_REALIZADA
        update_fields = ['confirmacao_realizacao', 'status']
        if observacoes is not None:
            sessao.observacoes = observacoes.strip()
            update_fields.append('observacoes')
        sessao.save(update_fields=update_fields)
        return Response(self.get_serializer(sessao).data)
