

from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from app import auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/csrf/', auth_views.csrf, name='api-csrf'),
    path('api/auth/login/', auth_views.login_web, name='api-login'),
    path('api/auth/session/', auth_views.sessao_atual, name='api-session'),
    path('api/auth/logout/', auth_views.logout_web, name='api-logout'),
    path(
        'api/schema/',
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name='api-schema',
    ),
    path(
        'api/docs',
        SpectacularSwaggerView.as_view(
            url_name='api-schema',
            permission_classes=[AllowAny],
        ),
        name='api-docs',
    ),
    path('api/', include('app.urls')),
]
