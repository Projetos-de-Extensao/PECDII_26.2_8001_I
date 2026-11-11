from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from app.models import Usuario


def criar_usuario(perfil, login, *, nome=None):
    """Cria uma conta autenticável com o perfil GAAP informado."""
    conta = get_user_model().objects.create_user(username=login)
    Usuario.objects.create(
        conta=conta,
        nome=nome or login,
        email=f'{login}@example.com',
        perfil=perfil,
    )
    return conta


def criar_perfil(perfil, login, *, nome=None):
    """Cria e devolve o perfil associado à conta autenticável."""
    return criar_usuario(perfil, login, nome=nome).usuario


def cliente_para(usuario):
    """Devolve um cliente de API autenticado por conta ou perfil de usuário."""
    client = APIClient()
    client.force_authenticate(user=getattr(usuario, 'conta', usuario))
    return client


def cliente_autenticado(perfil, login):
    """Devolve um cliente de API já autenticado com o perfil informado."""
    return cliente_para(criar_perfil(perfil, login))

