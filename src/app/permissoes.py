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
