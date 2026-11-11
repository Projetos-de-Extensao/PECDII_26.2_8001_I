from rest_framework.routers import DefaultRouter

from app.views import (
    AlunoViewSet,
    BloqueioAgendaViewSet,
    DisponibilidadeViewSet,
    ProfissionalViewSet,
    ServicoViewSet,
    SessaoViewSet,
)


# Registra os endpoints REST de cada recurso da API.
router = DefaultRouter()
router.register('alunos', AlunoViewSet, basename='aluno')
router.register('profissionais', ProfissionalViewSet, basename='profissional')
router.register('servicos', ServicoViewSet, basename='servico')
router.register('sessoes', SessaoViewSet, basename='sessao')
router.register('disponibilidades', DisponibilidadeViewSet, basename='disponibilidade')
router.register('bloqueios-agenda', BloqueioAgendaViewSet, basename='bloqueio-agenda')

urlpatterns = router.urls
