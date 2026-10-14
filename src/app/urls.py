from rest_framework.routers import DefaultRouter

from app.views import AlunoViewSet, ProdutoViewSet, SessaoViewSet


router = DefaultRouter()
router.register('produtos', ProdutoViewSet, basename='produto')
router.register('alunos', AlunoViewSet, basename='aluno')
router.register('sessoes', SessaoViewSet, basename='sessao')

urlpatterns = router.urls
