from rest_framework.routers import DefaultRouter

from app.views import AlunoViewSet, ProfessorViewSet, SessaoViewSet


# Registra os endpoints REST de cada recurso da API.
router = DefaultRouter()
router.register('alunos', AlunoViewSet, basename='aluno')
router.register('professores', ProfessorViewSet, basename='professor')
router.register('sessoes', SessaoViewSet, basename='sessao')

urlpatterns = router.urls
