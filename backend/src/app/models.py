from django.conf import settings
from django.core.exceptions import ValidationError
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
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name='sessoes',
        verbose_name='serviço',
    )
    profissional = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='sessoes',
        limit_choices_to={'perfil__in': ['TREINADOR', 'PROFISSIONAL_SAUDE']},
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
        indexes = [
            # Apoiam a busca de conflitos do profissional (RN-01) e dos alunos (RN-07), conforme o DER.
            models.Index(fields=['profissional', 'inicio', 'fim'], name='sessao_prof_inicio_fim_idx'),
            models.Index(fields=['inicio', 'fim'], name='sessao_inicio_fim_idx'),
        ]

    def __str__(self):
        """Retorna o título e o início da sessão para exibição."""
        return f'{self.titulo} — {self.inicio:%d/%m/%Y %H:%M}'


class Participacao(models.Model):
    """Liga um aluno a uma sessão e guarda a presença dele (RF-05, RF-06)."""

    class SituacaoPresenca(models.TextChoices):
        """Presença registrada depois da sessão; fica vazia até o registro."""

        PRESENTE = 'PRESENTE', 'Presente'
        FALTA = 'FALTA', 'Falta'

    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='sessão',
    )
    # PROTECT preserva o histórico de presença: o aluno não some das sessões ao ser removido.
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.PROTECT,
        related_name='participacoes',
    )
    situacao_presenca = models.CharField(
        'situação da presença',
        max_length=10,
        choices=SituacaoPresenca.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['sessao__inicio', 'aluno__nome']
        verbose_name = 'participação'
        verbose_name_plural = 'participações'
        constraints = [
            models.UniqueConstraint(
                fields=['sessao', 'aluno'],
                name='participacao_sessao_aluno_unico',
                violation_error_message='Este aluno já participa desta sessão.',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(situacao_presenca__isnull=True)
                    | models.Q(situacao_presenca__in=['PRESENTE', 'FALTA'])
                ),
                name='participacao_presenca_valida',
            ),
        ]
        indexes = [
            # Apoia a busca dos compromissos de um aluno (RN-07).
            models.Index(fields=['aluno', 'sessao'], name='participacao_aluno_sessao_idx'),
        ]

    def save(self, *args, **kwargs):
        """Valida a presença e a duplicidade antes de gravar, mesmo fora do admin."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Retorna o aluno e a sessão para exibição."""
        return f'{self.aluno} — {self.sessao}'


class RelatorioTreino(models.Model):
    """Relatório único de execução associado a uma sessão de Treino (RF-07)."""

    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    sessao = models.OneToOneField(
        Sessao,
        on_delete=models.CASCADE,
        related_name='relatorio_treino',
        verbose_name='sessão',
    )
    data = models.DateField(null=True, blank=True)
    horario = models.TimeField(null=True, blank=True)
    local = models.CharField(max_length=150, blank=True)
    objetivo = models.TextField(blank=True)
    exercicios = models.TextField(blank=True)
    volume_valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume_unidade = models.CharField(max_length=50, blank=True)
    intensidade_borg = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RASCUNHO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    finalizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'relatório de treino'
        verbose_name_plural = 'relatórios de treino'
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(intensidade_borg__isnull=True)
                           | models.Q(intensidade_borg__gte=0, intensidade_borg__lte=10)),
                name='relatorio_borg_entre_zero_e_dez',
            ),
            models.CheckConstraint(
                condition=models.Q(volume_valor__isnull=True) | models.Q(volume_valor__gte=0),
                name='relatorio_volume_nao_negativo',
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=['RASCUNHO', 'FINALIZADO']),
                name='relatorio_status_valido',
            ),
        ]

    def __str__(self):
        return f'Relatório de treino — sessão {self.sessao_id} ({self.get_status_display()})'


class NotificacaoEmail(models.Model):
    """Registra cada aviso enviado por e-mail sobre uma sessão, para não repeti-lo (RF-12)."""

    class Tipo(models.TextChoices):
        RELATORIO_PENDENTE = 'RELATORIO_PENDENTE', 'Relatório de treino pendente'

    sessao = models.ForeignKey(
        Sessao,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        verbose_name='sessão',
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    enviada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-enviada_em']
        verbose_name = 'notificação por e-mail'
        verbose_name_plural = 'notificações por e-mail'
        constraints = [
            # Duas execuções do comando não conseguem gravar o mesmo aviso para a mesma sessão.
            models.UniqueConstraint(fields=['sessao', 'tipo'], name='notificacao_sessao_tipo_unica'),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} — sessão {self.sessao_id}'


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

    def validar_perfil_com_vinculos(self):
        """Impede que quem atende serviços ou sessões passe a ter um perfil que não atende (RN-04)."""
        if not self.pk or self.perfil in self.PERFIS_PROFISSIONAIS:
            return
        if self.vinculos.exists():
            raise ValidationError({
                'perfil': 'Este usuário atende serviços. Remova os vínculos antes de mudar o perfil para Administrador.',
            })
        if self.sessoes.exists():
            raise ValidationError({
                'perfil': (
                    'Este usuário é responsável por sessões. Transfira as sessões para outro '
                    'profissional antes de mudar o perfil para Administrador.'
                ),
            })
        if self.disponibilidades.exists() or self.bloqueios_agenda.exists():
            raise ValidationError({
                'perfil': (
                    'Este usuário possui disponibilidade ou bloqueio de agenda. Remova esses '
                    'períodos antes de mudar o perfil para Administrador.'
                ),
            })

    def clean(self):
        """Valida o perfil nos formulários, como o do Django Admin."""
        super().clean()
        self.validar_perfil_com_vinculos()

    def save(self, *args, **kwargs):
        """Repete a checagem do perfil, porque o save() não passa pelo clean()."""
        self.validar_perfil_com_vinculos()
        super().save(*args, **kwargs)

    def __str__(self):
        """Retorna o nome do usuário para exibição."""
        return self.nome


class ProfissionalServico(models.Model):
    """Indica que um profissional está habilitado a atender um serviço (RN-04)."""

    profissional = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='vinculos',
        # Só Treinador e Profissional de Saúde atendem; o Administrador não tem serviço.
        limit_choices_to={'perfil__in': [perfil.value for perfil in Usuario.PERFIS_PROFISSIONAIS]},
        error_messages={
            'invalid': 'Apenas Treinador ou Profissional de Saúde podem ser vinculados a um serviço.',
        },
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.CASCADE,
        related_name='vinculos',
        verbose_name='serviço',
    )

    class Meta:
        ordering = ['servico__nome', 'profissional__nome']
        verbose_name = 'vínculo profissional-serviço'
        verbose_name_plural = 'vínculos profissional-serviço'
        constraints = [
            models.UniqueConstraint(
                fields=['profissional', 'servico'],
                name='profissional_servico_unico',
                violation_error_message='Este profissional já está vinculado a este serviço.',
            ),
        ]

    def save(self, *args, **kwargs):
        """Valida o perfil e a duplicidade antes de gravar, mesmo fora do admin."""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        """Retorna o par profissional e serviço para exibição."""
        return f'{self.profissional} — {self.servico}'


class Disponibilidade(models.Model):
    """Faixa em que um profissional pode atender, válida para todos os serviços."""

    profissional = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='disponibilidades',
        limit_choices_to={'perfil__in': [perfil.value for perfil in Usuario.PERFIS_PROFISSIONAIS]},
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    class Meta:
        ordering = ['inicio']
        verbose_name = 'disponibilidade'
        verbose_name_plural = 'disponibilidades'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fim__gt=models.F('inicio')),
                name='disponibilidade_fim_apos_inicio',
            ),
        ]
        indexes = [
            models.Index(fields=['profissional', 'inicio'], name='disp_prof_inicio_idx'),
        ]

    def clean(self):
        super().clean()
        if self.profissional_id and self.profissional.perfil not in Usuario.PERFIS_PROFISSIONAIS:
            raise ValidationError({
                'profissional': 'A disponibilidade deve pertencer a um Treinador ou Profissional de Saúde.'
            })
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({'fim': 'O fim da disponibilidade deve ser posterior ao início.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.profissional} — {self.inicio:%d/%m/%Y %H:%M} a {self.fim:%d/%m/%Y %H:%M}'


class BloqueioAgenda(models.Model):
    """Faixa bloqueada na agenda geral de um profissional."""

    profissional = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='bloqueios_agenda',
        limit_choices_to={'perfil__in': [perfil.value for perfil in Usuario.PERFIS_PROFISSIONAIS]},
    )
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    motivo = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['inicio']
        verbose_name = 'bloqueio de agenda'
        verbose_name_plural = 'bloqueios de agenda'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fim__gt=models.F('inicio')),
                name='bloqueio_fim_apos_inicio',
            ),
        ]
        indexes = [
            models.Index(fields=['profissional', 'inicio'], name='bloq_prof_inicio_idx'),
        ]

    def clean(self):
        super().clean()
        if self.profissional_id and self.profissional.perfil not in Usuario.PERFIS_PROFISSIONAIS:
            raise ValidationError({
                'profissional': 'O bloqueio deve pertencer a um Treinador ou Profissional de Saúde.'
            })
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError({'fim': 'O fim do bloqueio deve ser posterior ao início.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.profissional} — {self.inicio:%d/%m/%Y %H:%M} a {self.fim:%d/%m/%Y %H:%M}'
