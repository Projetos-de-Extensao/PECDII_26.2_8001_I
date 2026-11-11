from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as ValidacaoDjango
from rest_framework import serializers

from app.agendamento import confirmar_sessao
from app.models import (
    Aluno,
    BloqueioAgenda,
    Disponibilidade,
    Participacao,
    RegistroAuditoria,
    RelatorioTreino,
    Servico,
    Sessao,
    Usuario,
)
from app.operacao import TIPOS_DE_PENDENCIA
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

    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil__in=Usuario.PERFIS_PROFISSIONAIS),
    )
    servico = serializers.PrimaryKeyRelatedField(
        queryset=Servico.objects.all(),
        required=False,
    )
    # Os alunos são informados na confirmação e gravados junto com a sessão (RN-06).
    participantes = serializers.PrimaryKeyRelatedField(
        queryset=Aluno.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Sessao
        fields = [
            'id', 'titulo', 'tipo', 'descricao', 'observacoes', 'inicio', 'fim', 'servico', 'profissional',
            'participantes', 'status', 'notificacao_enviada_em',
        ]
        read_only_fields = ['id', 'notificacao_enviada_em']
        extra_kwargs = {
            'titulo': {'required': True},
            'tipo': {'required': True},
        }

    def to_representation(self, instance):
        """Lista os participantes pelo ID do aluno, como foram enviados, e a presença de cada um."""
        dados = super().to_representation(instance)
        participacoes = list(instance.participacoes.all())
        dados['participantes'] = [participacao.aluno_id for participacao in participacoes]
        dados['presencas'] = [
            {'aluno': participacao.aluno_id, 'situacao_presenca': participacao.situacao_presenca}
            for participacao in participacoes
        ]
        return dados

    def validate(self, attrs):
        """Valida horários e exige serviço, profissional e participantes ao confirmar."""
        inicio = attrs.get('inicio', getattr(self.instance, 'inicio', None))
        fim = attrs.get('fim', getattr(self.instance, 'fim', None))

        if inicio is not None and fim is not None and fim <= inicio:
            raise serializers.ValidationError({
                'fim': 'O fim da sessão deve ser posterior ao início.'
            })

        if self.instance:
            if 'participantes' in attrs:
                raise serializers.ValidationError({
                    'participantes': 'Os participantes são definidos na confirmação e não podem ser alterados.'
                })
            return attrs

        faltando = {}
        if not attrs.get('servico'):
            faltando['servico'] = 'Informe o serviço da sessão.'
        if not attrs.get('profissional'):
            faltando['profissional'] = 'Informe o profissional responsável pela sessão.'
        if not attrs.get('participantes'):
            faltando['participantes'] = 'Informe ao menos um aluno participante.'
        if faltando:
            raise serializers.ValidationError(faltando)

        alunos = attrs['participantes']
        if len({aluno.pk for aluno in alunos}) != len(alunos):
            raise serializers.ValidationError({
                'participantes': 'O mesmo aluno foi informado mais de uma vez.'
            })

        return attrs

    def create(self, validated_data):
        """Confirma a sessão e os participantes numa única transação."""
        alunos = validated_data.pop('participantes')
        return confirmar_sessao(validated_data, alunos)


class FiltroAgendaQueryParamsSerializer(serializers.Serializer):
    """Valida os filtros de período e serviço usados na consulta da agenda."""

    inicio = serializers.DateTimeField(required=False)
    fim = serializers.DateTimeField(required=False)
    servico = serializers.PrimaryKeyRelatedField(
        queryset=Servico.objects.all(),
        required=False,
    )

    def validate(self, attrs):
        inicio = attrs.get('inicio')
        fim = attrs.get('fim')
        if inicio is not None and fim is not None and fim <= inicio:
            raise serializers.ValidationError({
                'fim': 'O fim do período deve ser posterior ao início.'
            })
        return attrs


class FiltroPendenciasQueryParamsSerializer(serializers.Serializer):
    """Valida o filtro opcional por tipo de pendência (RF-09)."""

    tipo = serializers.ChoiceField(choices=list(TIPOS_DE_PENDENCIA.items()), required=False)


class PeriodoDashboardQueryParamsSerializer(serializers.Serializer):
    """Valida o período do dashboard: as duas datas juntas ou nenhuma (mês atual)."""

    inicio = serializers.DateField(required=False)
    fim = serializers.DateField(required=False)

    def validate(self, attrs):
        if ('inicio' in attrs) != ('fim' in attrs):
            raise serializers.ValidationError(
                'Informe inicio e fim juntos, ou nenhum dos dois para usar o mês atual.'
            )
        if 'inicio' in attrs and attrs['fim'] < attrs['inicio']:
            raise serializers.ValidationError({
                'fim': 'O fim do período não pode ser anterior ao início.'
            })
        return attrs


class SituacaoResumoSerializer(serializers.Serializer):
    """Rotulo exibido para cada situação de sessão no dashboard."""

    valor = serializers.ChoiceField(choices=Sessao.Status.choices)
    rotulo = serializers.CharField()


class ContagemSituacoesSerializer(serializers.Serializer):
    """Contagem de sessões agrupada pelas chaves de status da API."""

    por_situacao = serializers.DictField(child=serializers.IntegerField())
    total = serializers.IntegerField()


class ServicoDashboardSerializer(serializers.Serializer):
    """Resumo de um serviço no dashboard operacional."""

    id = serializers.IntegerField()
    nome = serializers.CharField()
    categoria = serializers.ChoiceField(choices=Servico.Categoria.choices)
    por_situacao = serializers.DictField(child=serializers.IntegerField())
    total = serializers.IntegerField()


class DashboardResponseSerializer(serializers.Serializer):
    """Resposta do dashboard administrativo."""

    periodo = PeriodoDashboardQueryParamsSerializer()
    situacoes = SituacaoResumoSerializer(many=True)
    servicos = ServicoDashboardSerializer(many=True)
    total = ContagemSituacoesSerializer()


class ServicoResumoPendenciaSerializer(serializers.Serializer):
    """Serviço associado a uma sessão pendente."""

    id = serializers.IntegerField()
    nome = serializers.CharField()
    categoria = serializers.ChoiceField(choices=Servico.Categoria.choices)


class SessaoResumoPendenciaSerializer(serializers.Serializer):
    """Resumo da sessão mostrado nos atalhos de pendências."""

    id = serializers.IntegerField()
    titulo = serializers.CharField()
    inicio = serializers.DateTimeField()
    fim = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=Sessao.Status.choices)
    servico = ServicoResumoPendenciaSerializer()


class ResponsavelPendenciaSerializer(serializers.Serializer):
    """Profissional responsável por uma pendência operacional."""

    id = serializers.IntegerField()
    nome = serializers.CharField()


class ItemPendenciaSerializer(serializers.Serializer):
    """Pendência individual com o atalho para a sessão ou relatório."""

    tipo = serializers.ChoiceField(choices=list(TIPOS_DE_PENDENCIA.items()))
    motivo = serializers.CharField()
    sessao = SessaoResumoPendenciaSerializer()
    responsavel = ResponsavelPendenciaSerializer()
    detalhe = serializers.CharField()


class TipoPendenciaSerializer(serializers.Serializer):
    """Rótulo de um tipo de pendência no filtro."""

    valor = serializers.ChoiceField(choices=list(TIPOS_DE_PENDENCIA.items()))
    rotulo = serializers.CharField()


class PendenciasResponseSerializer(serializers.Serializer):
    """Resposta da consulta operacional de pendências."""

    total = serializers.IntegerField()
    por_tipo = serializers.DictField(child=serializers.IntegerField())
    tipos = TipoPendenciaSerializer(many=True)
    itens = ItemPendenciaSerializer(many=True)


class FaixaAgendaSerializer(serializers.ModelSerializer):
    """Valida faixas da agenda e restringe o responsável a perfis profissionais."""

    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(perfil__in=Usuario.PERFIS_PROFISSIONAIS),
    )

    def validate(self, attrs):
        inicio = attrs.get('inicio', getattr(self.instance, 'inicio', None))
        fim = attrs.get('fim', getattr(self.instance, 'fim', None))
        if inicio is not None and fim is not None and fim <= inicio:
            raise serializers.ValidationError({
                'fim': f'O fim de {self.label_da_faixa} deve ser posterior ao início.'
            })
        return attrs


class DisponibilidadeSerializer(FaixaAgendaSerializer):
    """Converte períodos de disponibilidade para a API."""

    label_da_faixa = 'disponibilidade'

    class Meta:
        model = Disponibilidade
        fields = ['id', 'profissional', 'inicio', 'fim']
        read_only_fields = ['id']


class BloqueioAgendaSerializer(FaixaAgendaSerializer):
    """Converte períodos bloqueados para a API."""

    label_da_faixa = 'bloqueio'

    class Meta:
        model = BloqueioAgenda
        fields = ['id', 'profissional', 'inicio', 'fim', 'motivo']
        read_only_fields = ['id']
        extra_kwargs = {'motivo': {'required': False, 'allow_blank': True}}


class PresencaSerializer(serializers.Serializer):
    """Presença ou falta de um aluno participante."""

    aluno = serializers.IntegerField()
    situacao = serializers.ChoiceField(
        choices=Participacao.SituacaoPresenca.choices,
        error_messages={'invalid_choice': 'Informe PRESENTE ou FALTA.'},
    )


class RegistroPresencaSerializer(serializers.Serializer):
    """Valida o registro de presença de uma sessão (RF-06)."""

    presencas = PresencaSerializer(many=True, allow_empty=False)

    def validate_presencas(self, value):
        """Aceita só alunos da sessão, cada um uma vez."""
        alunos = [item['aluno'] for item in value]
        if len(set(alunos)) != len(alunos):
            raise serializers.ValidationError('O mesmo aluno foi informado mais de uma vez.')
        participantes = set(self.context['sessao'].participacoes.values_list('aluno_id', flat=True))
        fora_da_sessao = sorted(set(alunos) - participantes)
        if fora_da_sessao:
            raise serializers.ValidationError(
                f'Aluno(s) que não participam desta sessão: {", ".join(map(str, fora_da_sessao))}.'
            )
        return value


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    """Expõe os registros de auditoria somente para leitura (RNF-06)."""

    operacao_rotulo = serializers.CharField(source='get_operacao_display', read_only=True)

    class Meta:
        model = RegistroAuditoria
        fields = [
            'id', 'usuario', 'autor', 'operacao', 'operacao_rotulo', 'entidade', 'entidade_id',
            'mensagem', 'registrado_em',
        ]
        read_only_fields = fields


class RelatorioTreinoSerializer(serializers.ModelSerializer):
    """Valida rascunhos e expõe participantes a partir da sessão vinculada."""

    sessao = serializers.PrimaryKeyRelatedField(read_only=True)
    participantes = serializers.SerializerMethodField()

    CAMPOS_OBRIGATORIOS_FINALIZACAO = (
        'data',
        'horario',
        'local',
        'objetivo',
        'exercicios',
        'volume_valor',
        'volume_unidade',
        'intensidade_borg',
    )

    class Meta:
        model = RelatorioTreino
        fields = [
            'id', 'sessao', 'participantes', 'data', 'horario', 'local', 'objetivo', 'exercicios',
            'volume_valor', 'volume_unidade', 'intensidade_borg', 'status', 'criado_em',
            'atualizado_em', 'finalizado_em',
        ]
        read_only_fields = ['id', 'sessao', 'participantes', 'status', 'criado_em', 'atualizado_em', 'finalizado_em']

    def get_participantes(self, instance):
        return [
            {'id': participacao.aluno_id, 'nome': participacao.aluno.nome}
            for participacao in instance.sessao.participacoes.select_related('aluno')
        ]

    def validate(self, attrs):
        volume = attrs.get('volume_valor', getattr(self.instance, 'volume_valor', None))
        intensidade = attrs.get('intensidade_borg', getattr(self.instance, 'intensidade_borg', None))
        erros = {}
        if volume is not None and volume < 0:
            erros['volume_valor'] = 'O volume não pode ser negativo.'
        if intensidade is not None and not 0 <= intensidade <= 10:
            erros['intensidade_borg'] = 'Informe um valor entre 0 e 10 na escala Borg CR10.'
        if erros:
            raise serializers.ValidationError(erros)
        return attrs

    def validar_completo_para_finalizacao(self, dados_atualizados=None):
        """Exige todos os campos do RF-07 antes de tornar o relatório imutável."""
        dados_atualizados = dados_atualizados or {}
        faltando = {}
        for campo in self.CAMPOS_OBRIGATORIOS_FINALIZACAO:
            valor = dados_atualizados.get(
                campo,
                getattr(self.instance, campo, None) if self.instance is not None else None,
            )
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                faltando[campo] = 'Preencha este campo antes de finalizar o relatório.'
        if faltando:
            raise serializers.ValidationError(faltando)
