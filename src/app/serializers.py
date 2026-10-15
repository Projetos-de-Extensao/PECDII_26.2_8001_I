from rest_framework import serializers

from app.models import Aluno, Professor, Sessao
from app.telefones import formatar_telefone, normalizar_telefone


class TelefoneField(serializers.CharField):
    """Valida telefones com DDI e assume Brasil quando o DDI é omitido."""

    default_error_messages = {
        'invalid': 'Informe um telefone válido. Números sem DDI usam o Brasil como padrão.'
    }

    def to_internal_value(self, data):
        """Aceita telefone com ou sem máscara e devolve o formato padronizado."""
        value = super().to_internal_value(data)
        try:
            return normalizar_telefone(value)
        except ValueError:
            self.fail('invalid')

    def to_representation(self, value):
        """Retorna o telefone formatado conforme o país do DDI."""
        return formatar_telefone(value)


class AlunoSerializer(serializers.ModelSerializer):
    """Converte alunos entre modelos Django e JSON."""

    telefone = TelefoneField(required=False, allow_blank=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'data_nascimento', 'telefone']
        read_only_fields = ['id']


class ProfessorSerializer(serializers.ModelSerializer):
    """Converte professores entre modelos Django e JSON."""

    telefone = TelefoneField(required=False, allow_blank=True)

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
            'notificacao_enviada_em',
        ]
        read_only_fields = ['id', 'notificacao_enviada_em']
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
