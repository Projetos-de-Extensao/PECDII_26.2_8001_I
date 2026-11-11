from rest_framework.permissions import SAFE_METHODS, BasePermission

from app.models import Usuario


def perfil_da_conta(conta):
    """Retorna o perfil GAAP da conta autenticada, se houver."""
    usuario = getattr(conta, 'usuario', None)
    if usuario is not None:
        return usuario.perfil
    # O superusuário do Django administra o sistema antes de existir cadastro.
    if conta.is_superuser:
        return Usuario.Perfil.ADMINISTRADOR
    return None


class PodeAdministrarCadastros(BasePermission):
    """Libera consulta a qualquer perfil e alteração só ao Administrador."""

    message = 'Apenas o perfil Administrador pode alterar cadastros.'

    def has_permission(self, request, view):
        """Exige autenticação e, fora da leitura, o perfil Administrador."""
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return perfil_da_conta(request.user) == Usuario.Perfil.ADMINISTRADOR


class PodeConfirmarAgendamento(PodeAdministrarCadastros):
    """Libera a confirmação de agendamento só ao Administrador (RF-05, UC-05)."""

    message = 'Apenas o perfil Administrador pode confirmar agendamentos.'


class PodeRemoverSessao(PodeAdministrarCadastros):
    """Libera a remoção de sessões só ao Administrador."""

    message = 'Apenas o perfil Administrador pode remover sessões.'


class PodeAlterarSessao(BasePermission):
    """Libera a alteração da sessão ao Administrador e ao profissional responsável (RN-05, RF-10)."""

    message = 'Apenas o profissional responsável ou o Administrador pode alterar esta sessão.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if perfil_da_conta(request.user) == Usuario.Perfil.ADMINISTRADOR:
            return True
        usuario = getattr(request.user, 'usuario', None)
        return usuario is not None and obj.profissional_id == usuario.pk
