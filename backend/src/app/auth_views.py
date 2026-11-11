"""Endpoints de autenticação por sessão para o cliente web."""

import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from app.models import Servico, Usuario


def _dados_perfil(user):
    """Monta somente os dados de perfil que o cliente web precisa para navegar."""
    try:
        perfil = user.usuario
    except Usuario.DoesNotExist:
        perfil = None

    if perfil is None:
        if not (user.is_superuser or user.is_staff):
            return None
        return {
            'id': user.pk,
            'nome': user.get_full_name() or user.username,
            'email': user.email,
            'perfil': Usuario.Perfil.ADMINISTRADOR,
            'servicos': list(Servico.objects.order_by('nome').values('id', 'nome', 'categoria')),
        }

    if perfil.perfil == Usuario.Perfil.ADMINISTRADOR:
        servicos = Servico.objects.order_by('nome').values('id', 'nome', 'categoria')
    else:
        servicos = perfil.vinculos.select_related('servico').order_by('servico__nome').values(
            'servico_id', 'servico__nome', 'servico__categoria'
        )
        servicos = [
            {'id': item['servico_id'], 'nome': item['servico__nome'], 'categoria': item['servico__categoria']}
            for item in servicos
        ]

    return {
        'id': perfil.pk,
        'nome': perfil.nome,
        'email': perfil.email,
        'perfil': perfil.perfil,
        'servicos': list(servicos),
    }


def _ler_json(request):
    try:
        dados = json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return dados if isinstance(dados, dict) else None


@require_GET
@ensure_csrf_cookie
def csrf(request):
    """Entrega o token CSRF e define o cookie necessário para login/logout."""
    return JsonResponse({'csrfToken': get_token(request)})


@require_POST
@csrf_protect
def login_web(request):
    """Autentica por login ou e-mail sem expor credenciais ao armazenamento do cliente."""
    dados = _ler_json(request)
    if dados is None:
        return JsonResponse({'detail': 'Envie um objeto JSON válido.'}, status=400)
    identificador = dados.get('login')
    senha = dados.get('senha')
    if not isinstance(identificador, str) or not identificador.strip() or not isinstance(senha, str) or not senha:
        return JsonResponse({'detail': 'Informe login/e-mail e senha.'}, status=400)

    identificador = identificador.strip()
    user_model = get_user_model()
    conta_por_email = user_model.objects.filter(email__iexact=identificador).order_by('pk').first()
    username = conta_por_email.get_username() if conta_por_email else identificador
    user = authenticate(request, username=username, password=senha)
    if user is None:
        return JsonResponse({'detail': 'Login/e-mail ou senha incorretos.'}, status=401)
    dados_perfil = _dados_perfil(user)
    if dados_perfil is None:
        return JsonResponse({'detail': 'A conta não possui um perfil de acesso ao GAAP.'}, status=403)

    login(request, user)
    return JsonResponse(dados_perfil)


@require_GET
def sessao_atual(request):
    """Devolve o perfil autenticado, sem retornar informações da conta ou da senha."""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Autenticação necessária.'}, status=401)
    dados_perfil = _dados_perfil(request.user)
    if dados_perfil is None:
        return JsonResponse({'detail': 'A conta não possui um perfil de acesso ao GAAP.'}, status=403)
    return JsonResponse(dados_perfil)


@require_POST
@csrf_protect
def logout_web(request):
    """Encerra a sessão de autenticação do cliente web."""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Autenticação necessária.'}, status=401)
    logout(request)
    return JsonResponse({'detail': 'Sessão encerrada.'})
