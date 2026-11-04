from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ValidacaoDjango
from rest_framework import serializers

from app.models import Aluno, Professor, Servico, Sessao, Usuario
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


class ServicoSerializer(serializers.ModelSerializer):
    """Converte serviços entre modelos Django e JSON."""

    class Meta:
        model = Servico
        fields = ['id', 'nome', 'categoria']
        read_only_fields = ['id']
        extra_kwargs = {
            'categoria': {'required': True},
        }


class ProfissionalSerializer(serializers.ModelSerializer):
    """Converte profissionais e mantém a conta usada para acessar a API."""

    telefone = TelefoneField(required=False, allow_blank=True)
    login = serializers.CharField(max_length=150, write_only=True, required=False)
    senha = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'telefone', 'perfil', 'login', 'senha']
        read_only_fields = ['id']
        extra_kwargs = {
            'perfil': {'required': True},
        }

    def validate_perfil(self, value):
        """Aceita somente os perfis que atendem sessões no GAAP."""
        if value not in Usuario.PERFIS_PROFISSIONAIS:
            raise serializers.ValidationError(
                'Informe o perfil Treinador ou Profissional de Saúde.'
            )
        return value

    def validate_login(self, value):
        """Impede que duas contas usem o mesmo login."""
        contas = get_user_model().objects.filter(username=value)
        if self.instance:
            contas = contas.exclude(pk=self.instance.conta_id)
        if contas.exists():
            raise serializers.ValidationError('Este login já está em uso.')
        return value

    def validate_senha(self, value):
        """Aplica as regras de senha configuradas no projeto."""
        try:
            validate_password(value)
        except ValidacaoDjango as erro:
            raise serializers.ValidationError(list(erro.messages)) from erro
        return value

    def validate(self, attrs):
        """Exige login e senha ao cadastrar um profissional."""
        if self.instance:
            return attrs

        faltando = {
            campo: 'Informe este campo para criar a conta de acesso.'
            for campo in ('login', 'senha')
            if not attrs.get(campo)
        }
        if faltando:
            raise serializers.ValidationError(faltando)

        return attrs

    def create(self, validated_data):
        """Cria a conta de acesso guardando a senha somente como hash."""
        login = validated_data.pop('login')
        senha = validated_data.pop('senha')
        conta = get_user_model().objects.create_user(
            username=login,
            email=validated_data['email'],
            password=senha,
        )
        return Usuario.objects.create(conta=conta, **validated_data)

    def update(self, instance, validated_data):
        """Atualiza o cadastro e troca a senha apenas quando informada."""
        login = validated_data.pop('login', None)
        senha = validated_data.pop('senha', None)
        conta = instance.conta

        if login:
            conta.username = login
        if senha:
            conta.set_password(senha)
        if 'email' in validated_data:
            conta.email = validated_data['email']
        conta.save()

        return super().update(instance, validated_data)


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
