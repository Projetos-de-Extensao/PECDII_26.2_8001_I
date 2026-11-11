"""Funções compartilhadas para validar e formatar telefones internacionais."""

import phonenumbers
from phonenumbers import PhoneNumberFormat


def normalizar_telefone(valor, regiao_padrao='BR'):
    """Valida e armazena o telefone em formato internacional E.164."""
    if not valor:
        return ''

    try:
        telefone = phonenumbers.parse(str(valor), regiao_padrao)
    except phonenumbers.NumberParseException as erro:
        raise ValueError('Informe um telefone válido com DDI.') from erro

    if not phonenumbers.is_valid_number(telefone):
        raise ValueError('Informe um telefone válido com DDI.')

    return phonenumbers.format_number(telefone, PhoneNumberFormat.E164)


def formatar_telefone(valor, regiao_padrao='BR'):
    """Exibe o telefone no padrão internacional correspondente ao país."""
    if not valor:
        return ''

    try:
        telefone = phonenumbers.parse(str(valor), regiao_padrao)
    except phonenumbers.NumberParseException:
        return str(valor)

    if not phonenumbers.is_valid_number(telefone):
        return str(valor)

    return phonenumbers.format_number(telefone, PhoneNumberFormat.INTERNATIONAL)
