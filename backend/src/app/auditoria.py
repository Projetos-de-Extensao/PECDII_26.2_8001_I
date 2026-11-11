"""Trilha de auditoria das operações críticas (RNF-06)."""

from app.models import RegistroAuditoria

Operacao = RegistroAuditoria.Operacao


def registrar_auditoria(conta, operacao, objeto, acao):
    """Grava quem fez a operação, sobre qual registro e uma mensagem legível.

    `acao` completa a frase depois do nome do autor, por exemplo:
    'criou o usuário "Ana" com o perfil Treinador.'
    Nunca passe senhas, tokens ou outros dados de login na mensagem.
    """
    usuario = getattr(conta, 'usuario', None)
    autor = usuario.nome if usuario is not None else conta.get_username()
    return RegistroAuditoria.objects.create(
        usuario=usuario,
        autor=autor,
        operacao=operacao,
        entidade=type(objeto).__name__,
        entidade_id=objeto.pk,
        mensagem=f'{autor} {acao}',
    )
