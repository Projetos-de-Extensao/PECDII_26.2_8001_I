from rest_framework.routers import DefaultRouter

from app.views import ProdutoViewSet


router = DefaultRouter()
router.register('produtos', ProdutoViewSet, basename='produto')

urlpatterns = router.urls
