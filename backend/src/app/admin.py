from django.contrib import admin
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django import forms
from django.db.models import Count

from app.agendamento import CAPACIDADE_MAXIMA_SESSAO
from app.models import (
    Aluno,
    BloqueioAgenda,
    Disponibilidade,
    Participacao,
    ProfissionalServico,
    Servico,
    Sessao,
    Usuario,
)
from app.telefones import formatar_telefone, normalizar_telefone


class TelefoneAdminFormMixin:
    """Valida telefones internacionais inseridos pelo admin."""

    def __init__(self, *args, **kwargs):
        """Mostra números já salvos no padrão internacional legível."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['telefone'] = formatar_telefone(self.instance.telefone)

    def clean_telefone(self):
        try:
            return normalizar_telefone(self.cleaned_data.get('telefone'))
        except ValueError as erro:
            raise forms.ValidationError(str(erro)) from erro


class AlunoAdminForm(TelefoneAdminFormMixin, forms.ModelForm):
    """Formulário de aluno com telefone internacional validado."""

    class Meta:
        model = Aluno
        fields = '__all__'


class UsuarioAdminForm(TelefoneAdminFormMixin, forms.ModelForm):
    """Cria ou edita a conta de acesso junto com o perfil GAAP."""

    login = forms.CharField(label='Login', max_length=150)
    senha = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput,
        required=False,
    )
    perfil = forms.ChoiceField(
        label='Perfil de acesso',
        choices=(
            (Usuario.Perfil.ADMINISTRADOR, 'Coordenador (acesso administrativo)'),
            (Usuario.Perfil.TREINADOR, 'Professor/Treinador'),
            (Usuario.Perfil.PROFISSIONAL_SAUDE, 'Profissional de Saúde'),
        ),
        help_text=(
            'Somente o coordenador deve receber acesso administrativo. '
            'Professores/Treinadores usam o perfil Professor/Treinador.'
        ),
    )

    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'telefone', 'perfil')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_model = get_user_model()
        self.fields['login'].max_length = user_model._meta.get_field('username').max_length

        if self.instance and self.instance.pk:
            self.fields['login'].initial = self.instance.conta.get_username()
            self.fields['senha'].help_text = 'Deixe em branco para manter a senha atual.'
        else:
            self.fields['senha'].required = True
            self.fields['senha'].help_text = 'A senha será armazenada somente como hash.'

        self.order_fields(('login', 'senha', 'nome', 'email', 'telefone', 'perfil'))

    def clean_login(self):
        """Exige um login único sem diferenciar maiúsculas de minúsculas."""
        login = self.cleaned_data['login'].strip()
        contas = get_user_model()._default_manager.filter(username__iexact=login)
        if self.instance and self.instance.pk:
            contas = contas.exclude(pk=self.instance.conta_id)
        if contas.exists():
            raise forms.ValidationError('Já existe uma conta com este login.')
        return login

    def clean_senha(self):
        """Valida a senha inicial ou a nova senha antes de criar/atualizar a conta."""
        senha = self.cleaned_data.get('senha', '')
        if not senha:
            return senha

        conta = self.instance.conta if self.instance and self.instance.pk else None
        try:
            password_validation.validate_password(senha, user=conta)
        except ValidationError as erro:
            raise forms.ValidationError(erro.messages) from erro
        return senha


class SessaoAdminForm(forms.ModelForm):
    """Apresenta campos da sessão com rótulos em português correto."""

    class Meta:
        model = Sessao
        fields = '__all__'
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'observacoes': 'Observações',
            'inicio': 'Início',
            'fim': 'Fim',
            'status': 'Situação',
            'notificacao_enviada_em': 'Notificação enviada em',
        }


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Configura a listagem e busca de alunos no admin."""

    form = AlunoAdminForm
    list_display = ('nome', 'data_nascimento', 'telefone_formatado')
    search_fields = ('nome', 'telefone')
    ordering = ('nome',)

    @admin.display(description='Telefone')
    def telefone_formatado(self, obj):
        """Exibe o telefone do aluno conforme o país do DDI."""
        return formatar_telefone(obj.telefone)


class ProfissionalServicoInline(admin.TabularInline):
    """Lista, dentro do serviço, os profissionais habilitados a atendê-lo."""

    model = ProfissionalServico
    extra = 1
    verbose_name = 'profissional habilitado'
    verbose_name_plural = 'profissionais habilitados'


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    """Permite ao administrador manter o catálogo de serviços."""

    inlines = [ProfissionalServicoInline]
    list_display = ('nome', 'categoria', 'quantidade_de_profissionais')
    list_filter = ('categoria',)
    search_fields = ('nome',)
    ordering = ('nome',)

    def get_queryset(self, request):
        """Conta os profissionais de todos os serviços numa única consulta."""
        return super().get_queryset(request).annotate(total_profissionais=Count('vinculos'))

    @admin.display(description='Profissionais', ordering='total_profissionais')
    def quantidade_de_profissionais(self, obj):
        """Mostra quantos profissionais atendem o serviço."""
        return obj.total_profissionais


class ParticipacaoInline(admin.TabularInline):
    """Lista, dentro da sessão, os alunos participantes e a presença de cada um."""

    model = Participacao
    extra = 0
    # Mesmo limite da confirmação pela API (RN-02).
    max_num = CAPACIDADE_MAXIMA_SESSAO
    autocomplete_fields = ('aluno',)
    verbose_name = 'participante'
    verbose_name_plural = 'participantes'


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    """Configura filtros e colunas de sessões no admin."""

    form = SessaoAdminForm
    inlines = [ParticipacaoInline]
    readonly_fields = ('notificacao_enviada_em',)
    list_display = ('__str__', 'servico', 'profissional', 'inicio', 'fim', 'status')
    list_filter = ('servico', 'tipo', 'status')
    ordering = ('inicio',)

    def get_readonly_fields(self, request, obj=None):
        """Exibe o horário enviado como somente leitura após o cadastro."""
        if obj is None:
            return ()
        return self.readonly_fields

    def get_exclude(self, request, obj=None):
        """Oculta o controle de notificação ao cadastrar uma sessão."""
        campos_excluidos = list(super().get_exclude(request, obj) or [])
        if obj is None:
            campos_excluidos.append('notificacao_enviada_em')
        return campos_excluidos


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Configura perfis, contato e busca de usuários no admin."""

    form = UsuarioAdminForm
    fieldsets = (
        ('Conta de acesso', {'fields': ('login', 'senha')}),
        ('Perfil GAAP', {'fields': ('nome', 'email', 'telefone', 'perfil')}),
    )
    list_display = ('nome', 'login', 'email', 'perfil_exibicao', 'telefone_formatado')
    list_filter = ('perfil',)
    search_fields = ('nome', 'email', 'conta__username')
    ordering = ('nome',)

    def save_model(self, request, obj, form, change):
        """Salva credenciais e perfil numa única operação administrativa."""
        user_model = get_user_model()
        login = form.cleaned_data['login']
        senha = form.cleaned_data['senha']

        if change:
            conta = obj.conta
            conta.username = login
            conta.email = obj.email
            if senha:
                conta.set_password(senha)
            conta.save()
        else:
            obj.conta = user_model.objects.create_user(
                username=login,
                email=obj.email,
                password=senha,
            )

        super().save_model(request, obj, form, change)

    @admin.display(description='Login', ordering='conta__username')
    def login(self, obj):
        """Exibe e permite buscar o login da conta associada."""
        return obj.conta.get_username()

    @admin.display(description='Perfil', ordering='perfil')
    def perfil_exibicao(self, obj):
        """Distingue claramente o coordenador dos professores na listagem."""
        rotulos = {
            Usuario.Perfil.ADMINISTRADOR: 'Coordenador',
            Usuario.Perfil.TREINADOR: 'Professor/Treinador',
            Usuario.Perfil.PROFISSIONAL_SAUDE: 'Profissional de Saúde',
        }
        return rotulos.get(obj.perfil, obj.get_perfil_display())

    @admin.display(description='Telefone')
    def telefone_formatado(self, obj):
        """Exibe o telefone do usuário conforme o país do DDI."""
        return formatar_telefone(obj.telefone)


@admin.register(Disponibilidade)
class DisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ('profissional', 'inicio', 'fim')
    list_filter = ('profissional',)
    ordering = ('inicio',)


@admin.register(BloqueioAgenda)
class BloqueioAgendaAdmin(admin.ModelAdmin):
    list_display = ('profissional', 'inicio', 'fim', 'motivo')
    list_filter = ('profissional',)
    search_fields = ('motivo', 'profissional__nome')
    ordering = ('inicio',)
