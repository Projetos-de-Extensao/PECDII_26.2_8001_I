from django.contrib import admin

from app.models import Aluno, Produto, Sessao

admin.site.register(Produto)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_nascimento', 'telefone')
    search_fields = ('nome', 'telefone')
    ordering = ('nome',)


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'inicio', 'fim', 'status')
    list_filter = ('status',)
    ordering = ('inicio',)
