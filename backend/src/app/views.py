from datetime import timedelta

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as ValidacaoDjango
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
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
    validar_regras_da_agenda,
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
    AtualizarSessaoPatchRequestSerializer,
    AtualizarSessaoPutRequestSerializer,
    BloqueioAgendaSerializer,
    ConfirmarSessaoRequestSerializer,
    DashboardResponseSerializer,
    DisponibilidadeSerializer,
    FiltroAuditoriaQueryParamsSerializer,
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
        description='Lista os alunos cadastrados. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    ),
    retrieve=extend_schema(
        tags=['Alunos'], summary='Consultar aluno',
        description='Busca um aluno pelo identificador. Disponível a qualquer usuário autenticado.',
    ),
    create=extend_schema(
        tags=['Alunos'],
        summary='Cadastrar aluno',
        description='Cria o cadastro básico de um aluno. Somente o Administrador pode gravar. Data de nascimento no formato AAAA-MM-DD; telefone opcional.',
        examples=[OpenApiExample(
            'Novo aluno',
            value={'nome': 'Ana Lima', 'data_nascimento': '2010-03-01', 'telefone': '+5511999999999'},
            request_only=True,
        )],
    ),
    update=extend_schema(
        tags=['Alunos'], summary='Atualizar aluno',
        description='Substitui os dados do aluno. Somente o Administrador pode gravar.',
    ),
    partial_update=extend_schema(
        tags=['Alunos'], summary='Atualizar dados do aluno',
        description='Altera apenas os campos enviados. Somente o Administrador pode gravar.',
    ),
    destroy=extend_schema(
        tags=['Alunos'], summary='Remover aluno',
        description='Somente o Administrador pode remover o cadastro. A exclusão retorna 409 se o aluno participar de alguma sessão.',
        responses={
            204: None,
            403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'),
            409: OpenApiResponse(description='Aluno vinculado a uma ou mais sessões.'),
        },
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
        description='Lista Treinadores e Profissionais de Saúde. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    ),
    retrieve=extend_schema(
        tags=['Profissionais'], summary='Consultar profissional',
        description='Busca um profissional pelo identificador. Disponível a qualquer usuário autenticado.',
    ),
    create=extend_schema(
        tags=['Profissionais'],
        summary='Cadastrar profissional',
        description='Somente o Administrador pode criar o perfil profissional e sua conta de acesso. Login e senha são obrigatórios na criação. A senha é armazenada como hash e nunca retornada.',
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
        description='Somente o Administrador pode atualizar o cadastro. Login ou senha podem ser alterados quando informados; credenciais não são retornadas.',
    ),
    partial_update=extend_schema(
        tags=['Profissionais'], summary='Atualizar dados do profissional',
        description='Somente o Administrador pode gravar. Altera apenas os campos enviados; login ou senha só mudam quando informados e nunca são retornados.',
    ),
    destroy=extend_schema(
        tags=['Profissionais'], summary='Remover profissional',
        description='Somente o Administrador pode remover a conta e o perfil. A exclusão retorna 409 se o profissional estiver vinculado a alguma sessão.',
        responses={
            204: None,
            403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'),
            409: OpenApiResponse(description='Profissional responsável por uma ou mais sessões.'),
        },
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
        description='Lista os vínculos profissional-serviço. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    ),
    create=extend_schema(
        tags=['Habilitações'], summary='Habilitar profissional para serviço',
        description='Somente o Administrador pode criar o vínculo que autoriza o profissional a atender o serviço (RN-04). O par profissional-serviço deve ser único.',
        examples=[OpenApiExample(
            'Nova habilitação', value={'profissional': 2, 'servico': 3}, request_only=True,
        )],
    ),
    destroy=extend_schema(
        tags=['Habilitações'], summary='Remover habilitação',
        description='Somente o Administrador pode remover. A API retorna 409 se houver sessão não cancelada, futura ou em andamento, para esse profissional e serviço.',
        responses={
            204: None,
            403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'),
            409: OpenApiResponse(description='Habilitação necessária para uma sessão futura ou em andamento.'),
        },
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
    list=extend_schema(
        tags=['Serviços'], summary='Listar serviços',
        description='Lista os serviços cadastrados. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    ),
    retrieve=extend_schema(
        tags=['Serviços'], summary='Consultar serviço',
        description='Busca um serviço pelo identificador. Disponível a qualquer usuário autenticado.',
    ),
    create=extend_schema(
        tags=['Serviços'], summary='Cadastrar serviço',
        description='Somente o Administrador pode adicionar serviços ao catálogo. O nome deve ser único.',
        examples=[OpenApiExample(
            'Novo serviço', value={'nome': 'Treino funcional', 'categoria': 'TREINO'},
            request_only=True,
        )],
    ),
    update=extend_schema(
        tags=['Serviços'], summary='Atualizar serviço',
        description='Substitui os dados do serviço. Somente o Administrador pode gravar.',
    ),
    partial_update=extend_schema(
        tags=['Serviços'], summary='Atualizar dados do serviço',
        description='Altera apenas os campos enviados. Somente o Administrador pode gravar.',
    ),
    destroy=extend_schema(
        tags=['Serviços'], summary='Remover serviço',
        description='Somente o Administrador pode remover. A API retorna 409 se o serviço estiver vinculado a alguma sessão; vínculos profissional-serviço também são removidos.',
        responses={
            204: None,
            403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'),
            409: OpenApiResponse(description='Serviço vinculado a uma ou mais sessões.'),
        },
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
        description='Lista sessões no escopo do perfil autenticado: Administrador consulta todas; Treinador consulta as sessões sob sua responsabilidade; Profissional de Saúde consulta as sessões próprias de Fisioterapia, Psicologia ou Nutrição para as quais está habilitado. Os filtros de período e serviço são opcionais; profissionais só podem filtrar por serviço vinculado ao seu perfil.',
        parameters=[FiltroAgendaQueryParamsSerializer],
    ),
    retrieve=extend_schema(
        tags=['Sessões'], summary='Consultar sessão',
        description='Retorna os detalhes e a presença registrada para cada participante. O Administrador pode consultar qualquer sessão; Treinadores consultam sessões sob sua responsabilidade; Profissionais de Saúde consultam sessões próprias de Fisioterapia, Psicologia ou Nutrição para as quais estão habilitados.',
    ),
    create=extend_schema(
        tags=['Sessões'],
        summary='Confirmar sessão',
        description='Somente o Administrador pode confirmar. Informe serviço, profissional responsável e pelo menos um participante. A API valida disponibilidade, bloqueios, habilitação profissional, capacidade e conflitos do profissional e dos alunos antes de gravar; violações de agenda retornam 409 com regra e motivo.',
        request=ConfirmarSessaoRequestSerializer,
        responses={
            201: SessaoSerializer,
            400: OpenApiResponse(description='Campos ausentes, inválidos ou participantes duplicados.'),
            403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'),
            409: OpenApiResponse(description='Regra de agenda violada; resposta contém regra e motivo.'),
        },
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
        description='O Administrador pode alterar os dados da sessão; mudanças de horário, serviço ou responsável revalidam RN-01, RN-03, RN-04 e RN-07 na mesma transação. O profissional responsável pode alterar apenas status e observações; REALIZADA e NAO_REALIZADA só podem ser definidas a partir do fim previsto. Reativar uma sessão cancelada revalida as regras de agenda. Participantes não podem ser alterados. CANCELADA permanece um status disponível ao responsável, sem restrição temporal específica na regra atual.',
        request=AtualizarSessaoPutRequestSerializer,
        responses={
            200: SessaoSerializer,
            400: OpenApiResponse(description='Campos obrigatórios ou valores inválidos.'),
            403: OpenApiResponse(description='Somente Administrador ou profissional responsável pode alterar; o responsável tem campos limitados.'),
            409: OpenApiResponse(description='Conflito de agenda ou tentativa de registrar desfecho antes do fim previsto.'),
        },
    ),
    partial_update=extend_schema(
        tags=['Sessões'], summary='Atualizar dados da sessão',
        description='O Administrador pode alterar os campos enviados; mudanças de horário, serviço ou responsável revalidam RN-01, RN-03, RN-04 e RN-07 na mesma transação. O profissional responsável pode alterar apenas status e observações; REALIZADA e NAO_REALIZADA só podem ser definidas a partir do fim previsto. Reativar uma sessão cancelada revalida as regras de agenda. Participantes não podem ser alterados. CANCELADA permanece um status disponível ao responsável, sem restrição temporal específica na regra atual.',
        request=AtualizarSessaoPatchRequestSerializer,
        responses={
            200: SessaoSerializer,
            400: OpenApiResponse(description='Valores inválidos ou tentativa de alterar participantes.'),
            403: OpenApiResponse(description='Somente Administrador ou profissional responsável pode alterar; o responsável tem campos limitados.'),
            409: OpenApiResponse(description='Conflito de agenda ou tentativa de registrar desfecho antes do fim previsto.'),
        },
    ),
    destroy=extend_schema(
        tags=['Sessões'], summary='Remover sessão',
        description='Exclusivo do Administrador. A remoção também exclui participações e relatório vinculados à sessão.',
        responses={204: None, 403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.')},
    ),
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
        try:
            with transaction.atomic():
                sessao = Sessao.objects.select_for_update().select_related(
                    'profissional', 'servico',
                ).get(pk=serializer.instance.pk)
                serializer.instance = sessao
                perfil = perfil_da_conta(self.request.user)

                # A autorização de objeto é verificada também sob lock: outro administrador
                # pode ter trocado o responsável depois de get_object() validar a requisição.
                if perfil != Usuario.Perfil.ADMINISTRADOR:
                    usuario = getattr(self.request.user, 'usuario', None)
                    if usuario is None or sessao.profissional_id != usuario.pk:
                        raise PermissionDenied(
                            'Apenas o profissional responsável ou o Administrador pode alterar esta sessão.'
                        )

                novo_status = serializer.validated_data.get('status', sessao.status)
                if (
                    novo_status in (Sessao.Status.REALIZADA, Sessao.Status.NAO_REALIZADA)
                    and novo_status != sessao.status
                    and timezone.now() < sessao.fim
                ):
                    raise Conflito(self.MENSAGEM_SESSAO_NAO_ENCERRADA)

                if perfil != Usuario.Perfil.ADMINISTRADOR:
                    alterados = {
                        campo for campo, valor in serializer.validated_data.items()
                        if getattr(sessao, campo) != valor
                    }
                    if alterados - self.CAMPOS_DO_RESPONSAVEL:
                        raise PermissionDenied(
                            'O profissional responsável altera apenas a situação e as observações da sessão.'
                        )

                campos_da_agenda = {'inicio', 'fim', 'servico', 'profissional'}
                agenda_alterada = any(
                    campo in serializer.validated_data
                    and serializer.validated_data[campo] != getattr(sessao, campo)
                    for campo in campos_da_agenda
                )
                reativando_cancelada = (
                    sessao.status == Sessao.Status.CANCELADA
                    and novo_status != Sessao.Status.CANCELADA
                )
                if agenda_alterada or reativando_cancelada:
                    profissional_novo = serializer.validated_data.get('profissional', sessao.profissional)
                    ids_profissionais = {sessao.profissional_id, profissional_novo.pk}
                    list(
                        Usuario.objects.select_for_update()
                        .filter(pk__in=ids_profissionais)
                        .order_by('pk')
                    )
                    ids_alunos = list(
                        Participacao.objects.filter(sessao=sessao)
                        .order_by('aluno_id')
                        .values_list('aluno_id', flat=True)
                    )
                    alunos = list(
                        Aluno.objects.select_for_update()
                        .filter(pk__in=ids_alunos)
                        .order_by('pk')
                    )
                    dados = {
                        campo: serializer.validated_data.get(campo, getattr(sessao, campo))
                        for campo in ('inicio', 'fim', 'servico', 'profissional')
                    }
                    validar_regras_da_agenda(dados, alunos, sessao_ignorada=sessao.pk)

                serializer.save()
        except RegraDeAgendamentoViolada as erro:
            detalhes = {'regra': erro.regra, 'detail': erro.mensagem}
            sessao_conflitante = getattr(erro, 'sessao', None)
            if sessao_conflitante is not None:
                detalhes['sessao'] = sessao_conflitante.pk
            raise Conflito(detalhes) from erro

    @action(detail=True, methods=['patch'], url_path='presencas')
    @extend_schema(
        tags=['Sessões'], summary='Registrar presenças',
        description='Somente o profissional responsável registra PRESENTE ou FALTA para participantes da sessão. A sessão precisa ter chegado ao fim previsto e não pode estar cancelada. IDs repetidos e alunos fora da sessão são rejeitados.',
        request=RegistroPresencaSerializer,
        responses={
            200: SessaoSerializer,
            400: OpenApiResponse(description='Presenças vazias, inválidas, duplicadas ou de alunos que não participam da sessão.'),
            403: OpenApiResponse(description='Usuário autenticado que não é o profissional responsável.'),
            409: OpenApiResponse(description='Sessão ainda não encerrada ou cancelada.'),
        },
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
        description='Consulta o relatório da sessão. Disponível ao Administrador ou ao Treinador responsável; um relatório ausente retorna 404.',
        request=None,
        responses={
            200: RelatorioTreinoSerializer,
            403: OpenApiResponse(description='Somente Administrador ou Treinador responsável pode consultar.'),
            404: OpenApiResponse(description='A sessão ainda não tem relatório de treino.'),
        },
    )
    @extend_schema(
        methods=['POST', 'PATCH'],
        tags=['Relatórios'], summary='Criar ou editar relatório de treino',
        description='Somente o Treinador responsável pode criar ou editar um rascunho de sessão de Treino realizada e encerrada. Relatórios finalizados são imutáveis; POST duplicado, edição sem rascunho, sessão não realizada ou tentativa antes do fim retornam conflito.',
        request=RelatorioTreinoSerializer,
        responses={
            200: RelatorioTreinoSerializer,
            201: RelatorioTreinoSerializer,
            400: OpenApiResponse(description='Campos do relatório inválidos.'),
            403: OpenApiResponse(description='Somente o Treinador responsável pode criar ou editar.'),
            409: OpenApiResponse(description='Sessão não realizada, relatório finalizado ou operação em estado inválido.'),
        },
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
        description='Somente o Treinador responsável pode finalizar o relatório depois do fim da sessão. Exige todos os campos de execução e torna o relatório imutável.',
        request=RelatorioTreinoSerializer,
        responses={
            200: RelatorioTreinoSerializer,
            400: OpenApiResponse(description='Campos obrigatórios ausentes ou inválidos.'),
            403: OpenApiResponse(description='Somente o Treinador responsável pode finalizar.'),
            409: OpenApiResponse(description='Sessão em estado inválido ou relatório já finalizado.'),
        },
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


@extend_schema_view(
    retrieve=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Consultar disponibilidade',
        description='Consulta uma faixa de atendimento. Leitura disponível a qualquer usuário autenticado.',
    ),
    update=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Substituir disponibilidade',
        description='Somente o Administrador pode alterar a faixa. A mudança retorna 409 se deixar uma sessão ativa fora da disponibilidade.',
        responses={409: OpenApiResponse(description='A alteração deixaria uma sessão ativa sem cobertura de disponibilidade.')},
    ),
    partial_update=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Alterar disponibilidade',
        description='Somente o Administrador pode alterar os campos enviados. A mudança retorna 409 se deixar uma sessão ativa fora da disponibilidade.',
        responses={409: OpenApiResponse(description='A alteração deixaria uma sessão ativa sem cobertura de disponibilidade.')},
    ),
    destroy=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Remover disponibilidade',
        description='Somente o Administrador pode remover. A API retorna 409 se uma sessão ativa perder sua cobertura.',
        responses={204: None, 403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.'), 409: OpenApiResponse(description='A disponibilidade cobre uma sessão ativa.')},
    ),
)
class DisponibilidadeViewSet(ModelViewSet):
    """Gerencia períodos de disponibilidade com leitura autenticada e escrita administrativa."""

    queryset = Disponibilidade.objects.select_related('profissional').all()
    serializer_class = DisponibilidadeSerializer
    permission_classes = [PodeAdministrarCadastros]

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Listar disponibilidades',
        description='Consulta as faixas em que profissionais podem atender. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Criar disponibilidade',
        description='Somente o Administrador pode criar uma faixa de atendimento. O fim deve ser posterior ao início.',
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


@extend_schema_view(
    retrieve=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Consultar bloqueio',
        description='Consulta um bloqueio. Leitura disponível a qualquer usuário autenticado.',
    ),
    update=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Substituir bloqueio',
        description='Somente o Administrador pode alterar o bloqueio. A API retorna 409 se ele se sobrepuser a uma sessão ativa.',
        responses={409: OpenApiResponse(description='O bloqueio conflita com uma sessão ativa.')},
    ),
    partial_update=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Alterar bloqueio',
        description='Somente o Administrador pode alterar os campos enviados. A API retorna 409 se o intervalo se sobrepuser a uma sessão ativa.',
        responses={409: OpenApiResponse(description='O bloqueio conflita com uma sessão ativa.')},
    ),
    destroy=extend_schema(
        tags=['Agenda e disponibilidade'], summary='Remover bloqueio',
        description='Somente o Administrador pode remover o bloqueio.',
        responses={204: None, 403: OpenApiResponse(description='Usuário autenticado sem perfil Administrador.')},
    ),
)
class BloqueioAgendaViewSet(ModelViewSet):
    """Gerencia bloqueios com leitura autenticada e escrita administrativa."""

    queryset = BloqueioAgenda.objects.select_related('profissional').all()
    serializer_class = BloqueioAgendaSerializer
    permission_classes = [PodeAdministrarCadastros]

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Listar bloqueios',
        description='Consulta períodos indisponíveis na agenda dos profissionais. Qualquer usuário autenticado pode consultar; escrita restrita ao Administrador.',
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Agenda e disponibilidade'], summary='Criar bloqueio',
        description='Somente o Administrador pode bloquear um intervalo. O motivo é opcional; o fim deve ser posterior ao início. A API retorna 409 se o bloqueio se sobrepuser a uma sessão ativa.',
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
        description='Lista sessões encerradas não canceladas com participante sem presença/falta e sessões de Treino realizadas sem relatório finalizado. Inclui motivo, responsável e caminho de consulta do compromisso ou relatório. Somente leitura e exclusivo do Administrador.',
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
        description='Lista registros imutáveis de operações críticas. Exclusivo do Administrador. Filtros opcionais: operacao, entidade e entidade_id.',
        parameters=[FiltroAuditoriaQueryParamsSerializer],
    ),
    retrieve=extend_schema(
        tags=['Auditoria'], summary='Consultar evento de auditoria',
        description='Consulta um evento imutável. Exclusivo do Administrador.',
    ),
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
        filtros = FiltroAuditoriaQueryParamsSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        for filtro, valor in filtros.validated_data.items():
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
