from django.db import models

from app.telefones import normalizar_telefone


class TelefoneMixin:
    """Normaliza o telefone antes de salvar um modelo com contato."""

    def save(self, *args, **kwargs):
        self.telefone = normalizar_telefone(self.telefone)
        super().save(*args, **kwargs)


class Aluno(TelefoneMixin, models.Model):
    """Armazena os dados básicos de um aluno."""

    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        """Retorna o nome do aluno para exibição."""
        return self.nome


class Professor(TelefoneMixin, models.Model):
    """Armazena o contato do professor responsável pelas sessões."""

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'

    def __str__(self):
        """Retorna o nome do professor para exibição."""
        return self.nome


class Sessao(models.Model):
    """Representa um treinamento ou avaliação agendada."""

    class Tipo(models.TextChoices):
        """Tipos de sessão disponíveis na API."""

        TREINAMENTO = 'TREINAMENTO', 'Treinamento'
        AVALIACAO = 'AVALIACAO', 'Avaliação'

    class Status(models.TextChoices):
        """Situações possíveis para uma sessão."""

        AGENDADA = 'AGENDADA', 'Agendada'
        REALIZADA = 'REALIZADA', 'Realizada'
        NAO_REALIZADA = 'NAO_REALIZADA', 'Não realizada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    titulo = models.CharField(max_length=150, default='Sessão')
    descricao = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    tipo = models.CharField(
        max_length=12,
        choices=Tipo.choices,
        default=Tipo.TREINAMENTO,
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    professor = models.ForeignKey(
        Professor,
        on_delete=models.PROTECT,
        related_name='sessoes',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.AGENDADA,
    )
    notificacao_enviada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['inicio']
        verbose_name = 'sessão'
        verbose_name_plural = 'sessões'

    def __str__(self):
        """Retorna o título e o início da sessão para exibição."""
        return f'{self.titulo} — {self.inicio:%d/%m/%Y %H:%M}'
