from datetime import timedelta

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as ValidacaoDjango
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from app.auditoria import Operacao, registrar_auditoria
from app.agendamento import (
    RegraDeAgendamentoViolada,
    alterar_agenda,
    validar_bloqueio,
    validar_saida_de_disponibilidade,
)
from app.models import (
    Aluno,
    BloqueioAgenda,
    Disponibilidade,
    Participacao,
    ProfissionalServico,
    RegistroAuditoria,
    RelatorioTreino,
    Servico,
    Sessao,
    Usuario,
)
from app.operacao import mes_atual, pendencias_operacionais, resumo_por_servico
from app.permissoes import (
    PodeAdministrarCadastros,
    PodeAlterarSessao,
    PodeConfirmarAgendamento,
    PodeRemoverSessao,
    SomenteAdministrador,
    perfil_da_conta,
)
from app.serializers import (
    AlunoSerializer,
    BloqueioAgendaSerializer,
    DashboardResponseSerializer,
    DisponibilidadeSerializer,
    FiltroAgendaQueryParamsSerializer,
    FiltroPendenciasQueryParamsSerializer,
    PendenciasResponseSerializer,
    PeriodoDashboardQueryParamsSerializer,
    ProfissionalSerializer,
    ProfissionalServicoSerializer,
    RegistroAuditoriaSerializer,
    RelatorioTreinoSerializer,
    RegistroPresencaSerializer,
    ServicoSerializer,
    SessaoSerializer,
)


class Conflito(APIException):
    """Recusa uma operação que deixaria outros registros inconsistentes."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A operação conflita com registros existentes.'
    default_code = 'conflito'

    def __init__(self, detail=None, code=None):
        sessao_id = detail.get('sessao') if isinstance(detail, dict) else None
        super().__init__(detail, code)
        if sessao_id is not None:
            # APIException converte valores do dicionário em ErrorDetail (texto);
            # o contrato da API expõe o ID da sessão como inteiro.
            self.detail['sessao'] = sessao_id


def executar_alteracao_de_agenda(profissionais, validar, gravar):
    """Serializa a mudança da agenda e converte violações de regra em HTTP 409."""
    try:
        return alterar_agenda(profissionais, validar, gravar)
    except RegraDeAgendamentoViolada as erro:
        detalhes = {'regra': erro.regra, 'detail': erro.mensagem}
        sessao = getattr(erro, 'sessao', None)
        if sessao is not None:
            detalhes['sessao'] = sessao.pk
        raise Conflito(detalhes) from erro


@extend_schema_view(
    list=extend_schema(
        tags=['Alunos'],
        summary='Listar alunos',
        description='Retorna os alunos cadastrados. Operação restrita ao Administrador.',
    ),
    retrieve=extend_schema(
        tags=['Alunos'], summary='Consultar aluno',
        description='Busca um aluno pelo identificador.',
    ),
    create=extend_schema(
        tags=['Alunos'],
        summary='Cadastrar aluno',
        description='Cria o cadastro básico de um aluno. Data de nascimento no formato AAAA-MM-DD; telefone opcional.',
        examples=[OpenApiExample(
            'Novo aluno',
            value={'nome': 'Ana Lima', 'data_nascimento': '2010-03-01', 'telefone': '+5511999999999'},
            request_only=True,
        )],
    ),
    update=extend_schema(tags=['Alunos'], summary='Atualizar aluno'),
    partial_update=extend_schema(tags=['Alunos'], summary='Atualizar dados do aluno'),
    destroy=extend_schema(
        tags=['Alunos'], summary='Remover aluno',
        description='Remove o cadastro se ele não estiver vinculado a sessões.',
    ),
)
class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # As participações protegem o aluno; sem esta checagem o delete virava erro 500.
        if instance.participacoes.exists():
            raise Conflito(
                'Este aluno participa de sessões. Remova-o das sessões antes de excluir o cadastro.'
            )
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        tags=['Profissionais'], summary='Listar profissionais',
        description='Lista Treinadores e Profissionais de Saúde cadastrados.',
    ),
    retrieve=extend_schema(tags=['Profissionais'], summary='Consultar profissional'),
    create=extend_schema(
        tags=['Profissionais'],
        summary='Cadastrar profissional',
        description='Cria o perfil profissional e sua conta de acesso. Login e senha são obrigatórios na criação. A senha é armazenada como hash e nunca retornada.',
        examples=[OpenApiExample(
            'Novo treinador',
            value={
                'nome': 'Lucas Pereira', 'email': 'lucas@example.com',
                'telefone': '+5511999999999', 'perfil': 'TREINADOR',
                'login': 'lucas.pereira', 'senha': 'SenhaSegura123!',
            },
            request_only=True,
        )],
    ),
    update=extend_schema(
        tags=['Profissionais'], summary='Atualizar profissional',
        description='Atualiza o cadastro. Login ou senha podem ser alterados quando informados.',
    ),
    partial_update=extend_schema(
        tags=['Profissionais'], summary='Atualizar dados do profissional',
        description='Altera apenas os campos enviados; senha nova só é aplicada se informada.',
    ),
    destroy=extend_schema(
        tags=['Profissionais'], summary='Remover profissional',
        description='Remove a conta e o perfil se não houver sessões vinculadas.',
    ),
)
class ProfissionalViewSet(ModelViewSet):
    queryset = Usuario.objects.filter(perfil__in=Usuario.PERFIS_PROFISSIONAIS)
    serializer_class = ProfissionalSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_create(self, serializer):
        with transaction.atomic():
            usuario = serializer.save()
            registrar_auditoria(
                self.request.user,
                Operacao.USUARIO_CRIADO,
                usuario,
                f'criou o usuário "{usuario.nome}" com o perfil {usuario.get_perfil_display()}.',
            )

    def perform_destroy(self, instance):
        # As sessões protegem o responsável; sem esta checagem o delete virava erro 500.
        if instance.sessoes.exists():
            raise Conflito(
                'Este profissional é responsável por sessões. Transfira as sessões para outro '
                'profissional antes de removê-lo.'
            )
        # Apagar a conta encerra o acesso à API e remove o cadastro em cascata.
        instance.conta.delete()


@extend_schema_view(
    list=extend_schema(
        tags=['Habilitações'], summary='Listar profissionais habilitados para serviços',
    ),
    create=extend_schema(
        tags=['Habilitações'], summary='Habilitar profissional para serviço',
        description='Cria o vínculo que autoriza o profissional a atender o serviço (RN-04).',
        examples=[OpenApiExample(
            'Nova habilitação', value={'profissional': 2, 'servico': 3}, request_only=True,
        )],
    ),
    destroy=extend_schema(
        tags=['Habilitações'], summary='Remover habilitação',
        description='Recusa a remoção se houver sessão futura ou em andamento associada.',
    ),
)
class ProfissionalServicoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Administra quais profissionais podem prestar cada serviço."""

    queryset = ProfissionalServico.objects.select_related('profissional', 'servico')
    serializer_class = ProfissionalServicoSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_create(self, serializer):
        """Converte corrida de criação duplicada em conflito de domínio (409)."""
        with transaction.atomic():
            profissional = serializer.validated_data['profissional']
            Usuario.objects.select_for_update().get(pk=profissional.pk)
            try:
                serializer.save()
            except ValidacaoDjango as erro:
                detalhes = getattr(erro, 'message_dict', None) or erro.messages
                raise ValidationError(detalhes) from erro
            except IntegrityError as erro:
                raise Conflito('Este profissional já está vinculado a este serviço.') from erro

    def perform_destroy(self, instance):
        """Preserva a habilitação enquanto há sessão futura ou em andamento."""
        with transaction.atomic():
            Usuario.objects.select_for_update().get(pk=instance.profissional_id)
            vinculo = ProfissionalServico.objects.select_for_update().get(pk=instance.pk)
            existe_sessao_futura = Sessao.objects.filter(
                profissional_id=vinculo.profissional_id,
                servico_id=vinculo.servico_id,
                fim__gt=timezone.now(),
            ).exclude(status=Sessao.Status.CANCELADA).exists()
            if existe_sessao_futura:
                raise Conflito(
                    'Não é possível remover esta habilitação enquanto houver sessão futura '
                    'ou em andamento para esse profissional e serviço.'
                )
            vinculo.delete()


@extend_schema_view(
    list=extend_schema(tags=['Serviços'], summary='Listar serviços'),
    retrieve=extend_schema(tags=['Serviços'], summary='Consultar serviço'),
    create=extend_schema(
        tags=['Serviços'], summary='Cadastrar serviço',
        description='Adiciona um serviço ao catálogo. O nome deve ser único.',
        examples=[OpenApiExample(
            'Novo serviço', value={'nome': 'Treino funcional', 'categoria': 'TREINO'},
            request_only=True,
        )],
    ),
    update=extend_schema(tags=['Serviços'], summary='Atualizar serviço'),
    partial_update=extend_schema(tags=['Serviços'], summary='Atualizar dados do serviço'),
    destroy=extend_schema(
        tags=['Serviços'], summary='Remover serviço',
        description='Remove o serviço se não houver sessões vinculadas.',
    ),
)
class ServicoViewSet(ModelViewSet):
    queryset = Servico.objects.prefetch_related('vinculos')
    serializer_class = ServicoSerializer
    permission_classes = [PodeAdministrarCadastros]

    def perform_destroy(self, instance):
        # As sessões protegem o serviço; sem esta checagem o delete virava erro 500.
        if instance.sessoes.exists():
            raise Conflito(
                'Este serviço possui sessões agendadas ou realizadas e não pode ser excluído.'
            )
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        tags=['Sessões'], summary='Consultar agenda',
        description='Lista sessões no escopo permitido ao perfil autenticado. Os filtros de período e serviço são opcionais.',
        parameters=[FiltroAgendaQueryParamsSerializer],
    ),
    retrieve=extend_schema(
        tags=['Sessões'], summary='Consultar sessão',
        description='Retorna os detalhes e a presença registrada para cada participante.',
    ),
    create=extend_schema(
        tags=['Sessões'],
        summary='Confirmar sessão',
        description='Confirma um agendamento com serviço, profissional responsável e ao menos um participante. Disponibilidade, bloqueios e conflitos de agenda são validados antes de gravar.',
        examples=[OpenApiExample(
            'Sessão de treino',
            value={
                'titulo': 'Treino funcional', 'tipo': 'TREINAMENTO',
                'descricao': 'Treino de resistência',
                'inicio': '2026-11-12T14:00:00-03:00',
                'fim': '2026-11-12T15:00:00-03:00',
                'servico': 1, 'profissional': 2, 'participantes': [3, 4],
            },
            request_only=True,
        )],
    ),
    update=extend_schema(
        tags=['Sessões'], summary='Atualizar sessão',
        description='Atualiza os dados permitidos ao perfil. O profissional responsável pode alterar somente situação e observações.',
    ),
    partial_update=extend_schema(
        tags=['Sessões'], summary='Atualizar dados da sessão',
        description='Altera os campos enviados respeitando o escopo e as permissões do responsável.',
    ),
    destroy=extend_schema(tags=['Sessões'], summary='Remover sessão'),
    pendentes_status=extend_schema(
        tags=['Sessões'], summary='Listar sessões com situação pendente',
        description='Lista sessões ainda agendadas cujo horário previsto terminou há pelo menos 30 minutos.',
        parameters=[FiltroAgendaQueryParamsSerializer],
    ),
)
class SessaoViewSet(ModelViewSet):
    queryset = Sessao.objects.prefetch_related('participacoes')
    serializer_class = SessaoSerializer

    # Campos que o profissional responsável pode mudar: se a sessão foi ministrada (RF-10) e observações.
    CAMPOS_DO_RESPONSAVEL = {'status', 'observacoes'}
    MENSAGEM_SESSAO_NAO_ENCERRADA = 'A presença e a situação da sessão só podem ser registradas a partir do fim previsto.'

    def get_queryset(self):
        """Aplica o escopo da agenda e os filtros permitidos para cada perfil."""
        queryset = self.queryset.all().select_related('profissional', 'servico')
        usuario = getattr(self.request.user, 'usuario', None)
        if usuario is not None and usuario.perfil == Usuario.Perfil.PROFISSIONAL_SAUDE:
            queryset = queryset.filter(
                profissional=usuario,
                servico__categoria__in=[
                    Servico.Categoria.FISIOTERAPIA,
                    Servico.Categoria.PSICOLOGIA,
                    Servico.Categoria.NUTRICAO,
                ],
                servico__vinculos__profissional=usuario,
            )
        elif usuario is not None and usuario.perfil == Usuario.Perfil.TREINADOR:
            queryset = queryset.filter(profissional=usuario)

        if self.action in ('list', 'pendentes_status'):
            periodo = FiltroAgendaQueryParamsSerializer(data=self.request.query_params)
            periodo.is_valid(raise_exception=True)
            if 'inicio' in periodo.validated_data:
                queryset = queryset.filter(fim__gt=periodo.validated_data['inicio'])
            if 'fim' in periodo.validated_data:
                queryset = queryset.filter(inicio__lt=periodo.validated_data['fim'])
            if 'servico' in periodo.validated_data:
                servico = periodo.validated_data['servico']
                if (
                    usuario is not None
                    and usuario.perfil in (
                        Usuario.Perfil.TREINADOR,
                        Usuario.Perfil.PROFISSIONAL_SAUDE,
                    )
                    and not usuario.vinculos.filter(servico=servico).exists()
                ):
                    raise PermissionDenied('Só é possível filtrar por serviços vinculados ao seu perfil.')
                queryset = queryset.filter(servico=servico)

        return queryset.order_by('inicio', 'pk')

    def get_permissions(self):
        # Confirmar agendamento é do Administrador (UC-05), assim como remover sessões.
        if self.action == 'create':
            return [PodeConfirmarAgendamento()]
        if self.action == 'destroy':
            return [PodeRemoverSessao()]
        if self.action in ('update', 'partial_update'):
            return [PodeAlterarSessao()]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                sessao = serializer.save()
                registrar_auditoria(
                    self.request.user,
                    Operacao.AGENDAMENTO_CONFIRMADO,
                    sessao,
                    f'confirmou o agendamento "{sessao.titulo}" em '
                    f'{timezone.localtime(sessao.inicio):%d/%m/%Y às %H:%M} com '
                    f'{sessao.participacoes.count()} aluno(s), sob responsabilidade de {sessao.profissional.nome}.',
                )
        except RegraDeAgendamentoViolada as erro:
            raise Conflito({'regra': erro.regra, 'detail': erro.mensagem}) from erro

    def perform_update(self, serializer):
        sessao = serializer.instance
        novo_status = serializer.validated_data.get('status', sessao.status)
        if (
            novo_status in (Sessao.Status.REALIZADA, Sessao.Status.NAO_REALIZADA)
            and novo_status != sessao.status
            and timezone.now() < sessao.fim
        ):
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)
        if perfil_da_conta(self.request.user) != Usuario.Perfil.ADMINISTRADOR:
            alterados = {
                campo for campo, valor in serializer.validated_data.items()
                if getattr(sessao, campo) != valor
            }
            if alterados - self.CAMPOS_DO_RESPONSAVEL:
                raise PermissionDenied(
                    'O profissional responsável altera apenas a situação e as observações da sessão.'
                )
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='presencas')
    @extend_schema(
        tags=['Sessões'], summary='Registrar presenças',
        description='O profissional responsável registra PRESENTE ou FALTA para participantes da sessão encerrada. IDs repetidos e alunos fora da sessão são rejeitados.',
        request=RegistroPresencaSerializer,
        responses=SessaoSerializer,
        examples=[OpenApiExample(
            'Presenças da sessão',
            value={'presencas': [{'aluno': 3, 'situacao': 'PRESENTE'}, {'aluno': 4, 'situacao': 'FALTA'}]},
            request_only=True,
        )],
    )
    def presencas(self, request, pk=None):
        """Registra presença ou falta dos participantes (RF-06), só pelo responsável (RN-05)."""
        sessao = self.get_object()
        usuario = getattr(request.user, 'usuario', None)
        if usuario is None or sessao.profissional_id != usuario.pk:
            raise PermissionDenied('Apenas o profissional responsável pela sessão registra presença ou falta.')
        if sessao.status == Sessao.Status.CANCELADA:
            raise Conflito('Sessão cancelada não recebe registro de presença ou falta.')
        if timezone.now() < sessao.fim:
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)

        entrada = RegistroPresencaSerializer(data=request.data, context={'sessao': sessao})
        entrada.is_valid(raise_exception=True)
        with transaction.atomic():
            participacoes = {
                participacao.aluno_id: participacao
                for participacao in sessao.participacoes.select_for_update().select_related('aluno')
            }
            alteracoes = []
            for item in entrada.validated_data['presencas']:
                participacao = participacoes[item['aluno']]
                if participacao.situacao_presenca == item['situacao']:
                    continue
                participacao.situacao_presenca = item['situacao']
                participacao.save()
                rotulo = Participacao.SituacaoPresenca(item['situacao']).label
                alteracoes.append(f'{participacao.aluno.nome}: {rotulo.lower()}')
            # Só registra auditoria quando alguma presença realmente mudou.
            if alteracoes:
                registrar_auditoria(
                    request.user,
                    Operacao.PRESENCA_ALTERADA,
                    sessao,
                    f'registrou presença/falta na sessão "{sessao.titulo}" — {"; ".join(alteracoes)}.',
                )

        sessao = self.get_queryset().get(pk=sessao.pk)
        return Response(self.get_serializer(sessao).data)

    def _exigir_responsavel_treinador(self, sessao):
        usuario = getattr(self.request.user, 'usuario', None)
        if (
            usuario is None
            or usuario.perfil != Usuario.Perfil.TREINADOR
            or sessao.profissional_id != usuario.pk
        ):
            raise PermissionDenied('Somente o Treinador responsável pode criar ou alterar o relatório de treino.')

    def _validar_sessao_para_relatorio(self, sessao):
        if sessao.servico_id is None or sessao.servico.categoria != Servico.Categoria.TREINO:
            raise Conflito('O relatório de treino só pode ser associado a uma sessão do serviço Treino.')
        if sessao.status != Sessao.Status.REALIZADA:
            raise Conflito('A sessão precisa estar marcada como realizada antes de registrar o relatório.')
        if timezone.now() < sessao.fim:
            raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)

    @extend_schema(
        methods=['GET'],
        tags=['Relatórios'], summary='Consultar relatório de treino',
        description='Consulta o relatório da sessão. Disponível ao Administrador ou ao Treinador responsável.',
        request=None,
        responses=RelatorioTreinoSerializer,
    )
    @extend_schema(
        methods=['POST', 'PATCH'],
        tags=['Relatórios'], summary='Criar ou editar relatório de treino',
        description='Cria um rascunho com POST ou altera um rascunho com PATCH. O relatório pertence a uma sessão de Treino realizada; edição permitida apenas ao Treinador responsável.',
        request=RelatorioTreinoSerializer,
        responses=RelatorioTreinoSerializer,
        examples=[OpenApiExample(
            'Rascunho do relatório',
            value={
                'data': '2026-11-12', 'horario': '15:00:00', 'local': 'Centro esportivo',
                'objetivo': 'Desenvolver resistência', 'exercicios': 'Corrida leve; circuito funcional',
                'volume_valor': '45.00', 'volume_unidade': 'minutos', 'intensidade_borg': '6.0',
            },
            request_only=True,
        )],
    )
    @action(detail=True, methods=['get', 'post', 'patch'], url_path='relatorio')
    def relatorio(self, request, pk=None):
        """Consulta, cria ou edita o rascunho do relatório único da sessão de Treino."""
        sessao = self.get_object()
        perfil = perfil_da_conta(request.user)
        if request.method == 'GET':
            if perfil not in (Usuario.Perfil.ADMINISTRADOR, Usuario.Perfil.TREINADOR):
                raise PermissionDenied('Somente Administrador e Treinador podem consultar relatórios de treino.')
            if perfil == Usuario.Perfil.TREINADOR:
                self._exigir_responsavel_treinador(sessao)
            try:
                relatorio = sessao.relatorio_treino
            except RelatorioTreino.DoesNotExist as erro:
                raise NotFound('Esta sessão ainda não possui relatório de treino.') from erro
            return Response(RelatorioTreinoSerializer(relatorio).data)

        self._exigir_responsavel_treinador(sessao)
        self._validar_sessao_para_relatorio(sessao)
        with transaction.atomic():
            sessao = Sessao.objects.select_for_update().select_related('servico').get(pk=sessao.pk)
            if request.method == 'POST':
                if RelatorioTreino.objects.filter(sessao=sessao).exists():
                    raise Conflito('Esta sessão já possui um relatório de treino.')
                serializer = RelatorioTreinoSerializer(data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                try:
                    relatorio = serializer.save(sessao=sessao)
                except IntegrityError as erro:
                    raise Conflito('Esta sessão já possui um relatório de treino.') from erro
                return Response(RelatorioTreinoSerializer(relatorio).data, status=status.HTTP_201_CREATED)

            try:
                relatorio = RelatorioTreino.objects.select_for_update().get(sessao=sessao)
            except RelatorioTreino.DoesNotExist as erro:
                raise Conflito('Crie um rascunho antes de editar ou finalizar o relatório.') from erro
            if relatorio.status == RelatorioTreino.Status.FINALIZADO:
                raise Conflito('Relatórios finalizados são imutáveis.')
            serializer = RelatorioTreinoSerializer(relatorio, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            relatorio = serializer.save()
        return Response(RelatorioTreinoSerializer(relatorio).data)

    @action(detail=True, methods=['post'], url_path='relatorio/finalizar')
    @extend_schema(
        tags=['Relatórios'], summary='Finalizar relatório de treino',
        description='Exige todos os campos de execução e torna o relatório imutável. Permitido ao Treinador responsável.',
        request=RelatorioTreinoSerializer,
        responses=RelatorioTreinoSerializer,
    )
    def finalizar_relatorio(self, request, pk=None):
        """Valida todos os campos obrigatórios e finaliza o relatório em caráter imutável."""
        sessao = self.get_object()
        self._exigir_responsavel_treinador(sessao)
        self._validar_sessao_para_relatorio(sessao)
        with transaction.atomic():
            sessao = Sessao.objects.select_for_update().select_related('servico').get(pk=sessao.pk)
            try:
                relatorio = RelatorioTreino.objects.select_for_update().get(sessao=sessao)
            except RelatorioTreino.DoesNotExist as erro:
                raise Conflito('Crie um rascunho antes de finalizar o relatório.') from erro
            if relatorio.status == RelatorioTreino.Status.FINALIZADO:
                raise Conflito('Relatórios finalizados são imutáveis.')

            serializer = RelatorioTreinoSerializer(relatorio, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.validar_completo_para_finalizacao(serializer.validated_data)
            relatorio = serializer.save(
                status=RelatorioTreino.Status.FINALIZADO,
                finalizado_em=timezone.now(),
            )
            registrar_auditoria(
                request.user,
                Operacao.RELATORIO_FINALIZADO,
                relatorio,
                f'finalizou o relatório de treino da sessão "{sessao.titulo}".',
            )
        return Response(RelatorioTreinoSerializer(relatorio).data)

    @action(detail=False, methods=['get'], url_path='pendentes-status')
    @extend_schema(
        tags=['Sessões'], summary='Listar sessões com situação pendente',
        description='Lista sessões ainda agendadas cujo horário previsto terminou há pelo menos 30 minutos.',
        parameters=[FiltroAgendaQueryParamsSerializer],
        responses=SessaoSerializer(many=True),
    )
    def pendentes_status(self, request):
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = self.get_queryset().filter(
            status=Sessao.Status.AGENDADA,
            fim__lte=limite,
        )
        serializer = self.get_serializer(sessoes, many=True)
        return Response(serializer.data)


class DisponibilidadeViewSet(ModelViewSet):
    """Gerencia períodos de disponibilidade com leitura autenticada e escrita administrativa."""

    queryset = Disponibilidade.objects.select_related('profissional').all()
    serializer_class = DisponibilidadeSerializer
    permission_classes = [PodeAdministrarCadastros]

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Listar disponibilidades',
        description='Consulta as faixas em que profissionais podem atender. Escrita restrita ao Administrador.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Criar disponibilidade',
        description='Cria uma faixa de atendimento. O fim deve ser posterior ao início; mudanças que invalidem sessões existentes são recusadas.',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        instancia = serializer.instance
        profissional_novo = serializer.validated_data.get('profissional', instancia.profissional)
        profissionais = [instancia.profissional, profissional_novo]
        estado = {}

        def validar():
            atual = Disponibilidade.objects.select_for_update().get(pk=instancia.pk)
            estado['atual'] = atual
            serializer.instance = atual
            dados_novos = {
                'profissional': serializer.validated_data.get('profissional', atual.profissional),
                'inicio': serializer.validated_data.get('inicio', atual.inicio),
                'fim': serializer.validated_data.get('fim', atual.fim),
            }
            if any(
                dados_novos[campo] != getattr(atual, campo)
                for campo in ('profissional', 'inicio', 'fim')
            ):
                validar_saida_de_disponibilidade(atual, nova=dados_novos)

        executar_alteracao_de_agenda(profissionais, validar, serializer.save)

    def perform_destroy(self, instance):
        estado = {}

        def validar():
            atual = Disponibilidade.objects.select_for_update().get(pk=instance.pk)
            estado['atual'] = atual
            validar_saida_de_disponibilidade(atual)

        def excluir():
            estado['atual'].delete()

        executar_alteracao_de_agenda([instance.profissional], validar, excluir)


class BloqueioAgendaViewSet(ModelViewSet):
    """Gerencia bloqueios com leitura autenticada e escrita administrativa."""

    queryset = BloqueioAgenda.objects.select_related('profissional').all()
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [PodeAdministrarCadastros]

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Listar bloqueios',
        description='Consulta períodos indisponíveis na agenda dos profissionais. Escrita restrita ao Administrador.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Criar bloqueio',
        description='Bloqueia um intervalo da agenda. O motivo é opcional; o fim deve ser posterior ao início e o bloqueio não pode conflitar com sessões.',
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        dados = serializer.validated_data
        profissional = dados['profissional']
        executar_alteracao_de_agenda(
            [profissional],
            lambda: validar_bloqueio(profissional, dados['inicio'], dados['fim']),
            serializer.save,
        )

    def perform_update(self, serializer):
        instancia = serializer.instance
        profissional_novo = serializer.validated_data.get('profissional', instancia.profissional)
        profissionais = [instancia.profissional, profissional_novo]
        estado = {}

        def validar():
            atual = BloqueioAgenda.objects.select_for_update().get(pk=instancia.pk)
            estado['atual'] = atual
            serializer.instance = atual
            dados_novos = {
                'profissional': serializer.validated_data.get('profissional', atual.profissional),
                'inicio': serializer.validated_data.get('inicio', atual.inicio),
                'fim': serializer.validated_data.get('fim', atual.fim),
            }
            if any(
                dados_novos[campo] != getattr(atual, campo)
                for campo in ('profissional', 'inicio', 'fim')
            ):
                validar_bloqueio(
                    dados_novos['profissional'], dados_novos['inicio'], dados_novos['fim']
                )

        executar_alteracao_de_agenda(profissionais, validar, serializer.save)

    def perform_destroy(self, instance):
        def excluir():
            atual = BloqueioAgenda.objects.select_for_update().get(pk=instance.pk)
            atual.delete()

        executar_alteracao_de_agenda([instance.profissional], lambda: None, excluir)


class PendenciasView(APIView):
    """Pendências operacionais da agenda, exclusivas do Administrador (RF-09).

    É só consulta: o atalho `detalhe` abre a sessão ou o relatório, mas presença e relatório
    continuam sendo alterados apenas pelo profissional responsável (RN-05).
    """

    permission_classes = [SomenteAdministrador]

    @extend_schema(
        tags=['Operação'], summary='Consultar pendências operacionais',
        description='Lista sessões encerradas sem situação e sessões de Treino realizadas sem relatório finalizado. Somente leitura e exclusivo do Administrador.',
        parameters=[FiltroPendenciasQueryParamsSerializer],
        responses=PendenciasResponseSerializer,
    )
    def get(self, request):
        filtro = FiltroPendenciasQueryParamsSerializer(data=request.query_params)
        filtro.is_valid(raise_exception=True)
        return Response(pendencias_operacionais(tipo=filtro.validated_data.get('tipo')))


@extend_schema_view(
    list=extend_schema(
        tags=['Auditoria'], summary='Consultar trilha de auditoria',
        description='Lista registros imutáveis de operações críticas. Exclusivo do Administrador.',
    ),
    retrieve=extend_schema(tags=['Auditoria'], summary='Consultar evento de auditoria'),
)
class AuditoriaViewSet(ReadOnlyModelViewSet):
    """Consulta da trilha de auditoria, exclusiva do Administrador (RNF-06).

    É somente leitura: a API não oferece criação, alteração nem exclusão de registros.
    Filtros opcionais: ?operacao=, ?entidade= e ?entidade_id=.
    """

    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [SomenteAdministrador]

    def get_queryset(self):
        queryset = RegistroAuditoria.objects.all()
        entidade_id = self.request.query_params.get('entidade_id')
        if entidade_id and not entidade_id.isdigit():
            raise ValidationError({'entidade_id': 'Informe um número inteiro.'})
        for filtro in ('operacao', 'entidade', 'entidade_id'):
            valor = self.request.query_params.get(filtro)
            if valor:
                queryset = queryset.filter(**{filtro: valor})
        return queryset


class DashboardView(APIView):
    """Dashboard simples da operação, exclusivo do Administrador (RF-11)."""

    permission_classes = [SomenteAdministrador]

    @extend_schema(
        tags=['Operação'], summary='Consultar dashboard',
        description='Resume sessões por serviço e situação. Sem datas, considera o mês atual; para definir outro período, envie inicio e fim juntos no formato AAAA-MM-DD. Exclusivo do Administrador.',
        parameters=[PeriodoDashboardQueryParamsSerializer],
        responses=DashboardResponseSerializer,
    )
    def get(self, request):
        periodo = PeriodoDashboardQueryParamsSerializer(data=request.query_params)
        periodo.is_valid(raise_exception=True)
        inicio, fim = mes_atual()
        inicio = periodo.validated_data.get('inicio', inicio)
        fim = periodo.validated_data.get('fim', fim)
        return Response(resumo_por_servico(inicio, fim))
