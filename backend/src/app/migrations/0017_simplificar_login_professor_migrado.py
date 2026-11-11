"""Simplifica os logins internos criados ao migrar os antigos professores."""

from django.conf import settings
from django.db import migrations


PREFIXO_ANTIGO = 'gaap-migrado-professor-'


def _modelo_conta(apps):
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    return apps.get_model(app_label, model_name)


def simplificar_logins(apps, schema_editor):
    """Remove o prefixo técnico sem alterar os perfis nem as credenciais."""
    alias = schema_editor.connection.alias
    Conta = _modelo_conta(apps)
    contas = list(
        Conta.objects.using(alias)
        .filter(username__startswith=PREFIXO_ANTIGO)
        .order_by('pk')
    )
    ids_origem = {conta.pk for conta in contas}
    alteracoes = []
    nomes_destino = set()

    for conta in contas:
        sufixo = conta.username[len(PREFIXO_ANTIGO):]
        if not sufixo.isdigit():
            raise RuntimeError(
                f'Não foi possível simplificar o login {conta.username!r}: '
                'o identificador do professor não é numérico.'
            )

        professor_id = int(sufixo)
        novo_login = 'usuario' if professor_id == 1 else f'usuario-{professor_id}'
        if novo_login.casefold() in nomes_destino:
            raise RuntimeError(
                f'Não foi possível simplificar os logins: {novo_login!r} foi gerado mais de uma vez.'
            )
        if (
            Conta.objects.using(alias)
            .filter(username__iexact=novo_login)
            .exclude(pk__in=ids_origem)
            .exists()
        ):
            raise RuntimeError(
                f'Não foi possível renomear {conta.username!r} para {novo_login!r}: '
                'esse login já pertence a outra conta. Altere o login conflitante e tente novamente.'
            )

        nomes_destino.add(novo_login.casefold())
        alteracoes.append((conta.pk, novo_login))

    for conta_id, novo_login in alteracoes:
        Conta.objects.using(alias).filter(pk=conta_id).update(username=novo_login)


def restaurar_logins(apps, schema_editor):
    """Restaura os nomes internos se a migração for revertida."""
    alias = schema_editor.connection.alias
    Conta = _modelo_conta(apps)
    contas = list(Conta.objects.using(alias).filter(username__startswith='usuario'))
    alteracoes = []
    ids_origem = {conta.pk for conta in contas}

    for conta in contas:
        if conta.username == 'usuario':
            professor_id = 1
        elif conta.username.startswith('usuario-'):
            sufixo = conta.username.removeprefix('usuario-')
            if not sufixo.isdigit():
                continue
            professor_id = int(sufixo)
        else:
            continue

        login_original = f'{PREFIXO_ANTIGO}{professor_id}'
        if (
            Conta.objects.using(alias)
            .filter(username__iexact=login_original)
            .exclude(pk__in=ids_origem)
            .exists()
        ):
            raise RuntimeError(
                f'Não foi possível restaurar {conta.username!r} para {login_original!r}: '
                'esse login já pertence a outra conta.'
            )
        alteracoes.append((conta.pk, login_original))

    for conta_id, login_original in alteracoes:
        Conta.objects.using(alias).filter(pk=conta_id).update(username=login_original)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_relatorio_treino'),
    ]

    operations = [
        migrations.RunPython(simplificar_logins, restaurar_logins),
    ]
