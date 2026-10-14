from rest_framework import serializers

from app.models import Aluno, Produto, Sessao


class ProdutoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'preco', 'descricao', 'disponivel']
        read_only_fields = ['id']


class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'data_nascimento', 'telefone']
        read_only_fields = ['id']


class SessaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sessao
        fields = ['id', 'inicio', 'fim', 'status']
        read_only_fields = ['id']

    def validate(self, attrs):
        inicio = attrs.get('inicio', getattr(self.instance, 'inicio', None))
        fim = attrs.get('fim', getattr(self.instance, 'fim', None))

        if inicio is not None and fim is not None and fim <= inicio:
            raise serializers.ValidationError({
                'fim': 'O fim da sessão deve ser posterior ao início.'
            })

        return attrs
