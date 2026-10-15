from rest_framework import serializers

from app.models import Aluno, Professor, Sessao


class TelefoneBrasileiroField(serializers.CharField):
    """Normaliza celular brasileiro de 11 dígitos para o padrão +55 (DD) 9XXXX-XXXX."""

    default_error_messages = {
        'invalid': 'Informe um celular com DDD e 9 dígitos, opcionalmente com DDI 55.'
    }

    def to_internal_value(self, data):
        """Aceita telefone com ou sem máscara e devolve o formato padronizado."""
        value = super().to_internal_value(data)
        digits = ''.join(character for character in value if character.isdigit())

        if len(digits) == 13 and digits.startswith('55'):
            digits = digits[2:]

        if len(digits) != 11 or digits[0] == '0' or digits[2] != '9':
            self.fail('invalid')

        return f'+55 ({digits[:2]}) {digits[2:7]}-{digits[7:]}'


class AlunoSerializer(serializers.ModelSerializer):
    """Converte alunos entre modelos Django e JSON."""

    telefone = TelefoneBrasileiroField(required=False, allow_blank=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'data_nascimento', 'telefone']
        read_only_fields = ['id']


class ProfessorSerializer(serializers.ModelSerializer):
    """Converte professores entre modelos Django e JSON."""

    telefone = TelefoneBrasileiroField(required=False, allow_blank=True)

    class Meta:
        model = Professor
        fields = ['id', 'nome', 'email', 'telefone']
        read_only_fields = ['id']


class SessaoSerializer(serializers.ModelSerializer):
    """Valida e converte sessões para a API REST."""

    class Meta:
        model = Sessao
        fields = [
            'id', 'titulo', 'tipo', 'descricao', 'observacoes', 'inicio', 'fim', 'professor', 'status',
            'confirmacao_realizacao', 'notificacao_enviada_em',
        ]
        read_only_fields = ['id', 'confirmacao_realizacao', 'notificacao_enviada_em']
        extra_kwargs = {
            'titulo': {'required': True},
            'tipo': {'required': True},
        }

    def validate(self, attrs):
        """Valida horários e exige professor ao criar uma sessão."""
        inicio = attrs.get('inicio', getattr(self.instance, 'inicio', None))
        fim = attrs.get('fim', getattr(self.instance, 'fim', None))

        if inicio is not None and fim is not None and fim <= inicio:
            raise serializers.ValidationError({
                'fim': 'O fim da sessão deve ser posterior ao início.'
            })

        if not self.instance and not attrs.get('professor'):
            raise serializers.ValidationError({
                'professor': 'Informe o professor responsável pela sessão.'
            })

        return attrs
