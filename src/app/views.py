from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.models import Aluno, Produto, Sessao
from app.serializers import AlunoSerializer, ProdutoSerializer, SessaoSerializer


class ProdutoViewSet(ModelViewSet):
    queryset = Produto.objects.all().order_by('id')
    serializer_class = ProdutoSerializer

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        produtos = self.queryset.filter(disponivel=True)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def baratos(self, request):
        produtos = self.queryset.filter(preco__lt=Decimal('1000.00'))
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer


class SessaoViewSet(ModelViewSet):
    queryset = Sessao.objects.all()
    serializer_class = SessaoSerializer
