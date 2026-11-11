

from django.contrib import admin
from django.urls import path, include

from app import auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/csrf/', auth_views.csrf, name='api-csrf'),
    path('api/auth/login/', auth_views.login_web, name='api-login'),
    path('api/auth/session/', auth_views.sessao_atual, name='api-session'),
    path('api/auth/logout/', auth_views.logout_web, name='api-logout'),
    path('api/', include('app.urls')),
]
