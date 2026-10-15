from django.contrib import admin

from app.models import Aluno, Professor, Sessao


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    """Configura contatos e busca de professores no admin."""

    list_display = ('nome', 'email', 'telefone')
    search_fields = ('nome', 'email', 'telefone')
    ordering = ('nome',)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """Configura a listagem e busca de alunos no admin."""

    list_display = ('nome', 'data_nascimento', 'telefone')
    search_fields = ('nome', 'telefone')
    ordering = ('nome',)


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    """Configura filtros e colunas de sessões no admin."""

    list_display = ('__str__', 'tipo', 'professor', 'inicio', 'fim', 'status')
    list_filter = ('tipo', 'status', 'confirmacao_realizacao')
    ordering = ('inicio',)
