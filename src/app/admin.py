from django.contrib import admin
from django import forms

from app.models import Aluno, Professor, Sessao
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


class ProfessorAdminForm(TelefoneAdminFormMixin, forms.ModelForm):
    """Formulário de professor com telefone internacional validado."""

    class Meta:
        model = Professor
        fields = '__all__'


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


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Configura contatos e busca de professores no admin."""

    form = ProfessorAdminForm
    list_display = ('nome', 'email', 'telefone_formatado')
    search_fields = ('nome', 'email', 'telefone')
    ordering = ('nome',)

    @admin.display(description='Telefone')
    def telefone_formatado(self, obj):
        """Exibe o telefone do professor conforme o país do DDI."""
        return formatar_telefone(obj.telefone)


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


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    """Configura filtros e colunas de sessões no admin."""

    form = SessaoAdminForm
    readonly_fields = ('notificacao_enviada_em',)
    list_display = ('__str__', 'tipo', 'professor', 'inicio', 'fim', 'status')
    list_filter = ('tipo', 'status')
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