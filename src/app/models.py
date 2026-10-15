from django.db import models

class Aluno(models.Model):
    """Armazena os dados básicos de um aluno."""

    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        """Retorna o nome do aluno para exibição."""
        return self.nome


class Professor(models.Model):
    """Armazena o contato do professor responsável pelas sessões."""

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']

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

    class Confirmacao(models.TextChoices):
        """Respostas do professor sobre a realização da sessão."""

        PENDENTE = 'PENDENTE', 'Pendente'
        OCORREU = 'OCORREU', 'Ocorreu'
        NAO_OCORREU = 'NAO_OCORREU', 'Não ocorreu'

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
    confirmacao_realizacao = models.CharField(
        max_length=12,
        choices=Confirmacao.choices,
        default=Confirmacao.PENDENTE,
    )
    notificacao_enviada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['inicio']
        verbose_name = 'sessão'
        verbose_name_plural = 'sessões'

    def __str__(self):
        """Retorna o título e o início da sessão para exibição."""
        return f'{self.titulo} — {self.inicio:%d/%m/%Y %H:%M}'
