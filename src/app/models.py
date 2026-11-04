from django.conf import settings
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


class Servico(models.Model):
    """Serviço oferecido pela escola, como um treino ou uma consulta."""

    class Categoria(models.TextChoices):
        """Áreas de atendimento previstas no cenário GAAP."""

        TREINO = 'TREINO', 'Treino'
        FISIOTERAPIA = 'FISIOTERAPIA', 'Fisioterapia'
        PSICOLOGIA = 'PSICOLOGIA', 'Psicologia'
        NUTRICAO = 'NUTRICAO', 'Nutrição'

    nome = models.CharField(
        max_length=100,
        unique=True,
        error_messages={'unique': 'Já existe um serviço com este nome.'},
    )
    categoria = models.CharField(max_length=20, choices=Categoria.choices)

    class Meta:
        ordering = ['nome']
        verbose_name = 'serviço'
        verbose_name_plural = 'serviços'
        constraints = [
            # Garante a categoria também em gravações que não passam pela validação do Django.
            models.CheckConstraint(
                condition=models.Q(categoria__in=['TREINO', 'FISIOTERAPIA', 'PSICOLOGIA', 'NUTRICAO']),
                name='servico_categoria_valida',
            ),
        ]

    def save(self, *args, **kwargs):
        """Remove espaços nas pontas para que 'Pilates ' e 'Pilates' não convivam."""
        self.nome = (self.nome or '').strip()
        super().save(*args, **kwargs)

    def clean_fields(self, exclude=None):
        """Limpa o nome antes das validações, para que um nome só de espaços conte como vazio."""
        self.nome = (self.nome or '').strip()
        super().clean_fields(exclude)

    def __str__(self):
        """Retorna o nome do serviço para exibição."""
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


class Usuario(TelefoneMixin, models.Model):
    """Guarda o perfil GAAP da conta que acessa a API."""

    class Perfil(models.TextChoices):
        """Perfis de acesso previstos no GAAP."""

        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        TREINADOR = 'TREINADOR', 'Treinador'
        PROFISSIONAL_SAUDE = 'PROFISSIONAL_SAUDE', 'Profissional de Saúde'

    # Perfis que atendem sessões e aparecem no cadastro de profissionais.
    PERFIS_PROFISSIONAIS = [Perfil.TREINADOR, Perfil.PROFISSIONAL_SAUDE]

    conta = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usuario',
    )
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    perfil = models.CharField(max_length=20, choices=Perfil.choices)

    class Meta:
        ordering = ['nome']
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        """Retorna o nome do usuário para exibição."""
        return self.nome
