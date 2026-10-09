from rest_framework.viewsets import ModelViewSet

from app.models import Produto
from app.serializers import ProdutoSerializer


class ProdutoViewSet(ModelViewSet):
    queryset = Produto.objects.all().order_by('id')
    serializer_class = ProdutoSerializer