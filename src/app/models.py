from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    descricao = models.TextField()
    disponivel = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Aluno(models.Model):
    nome = models.CharField(max_length=150)
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Sessao(models.Model):
    class Status(models.TextChoices):
        AGENDADA = 'AGENDADA', 'Agendada'
        REALIZADA = 'REALIZADA', 'Realizada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.AGENDADA,
    )

    class Meta:
        ordering = ['inicio']

    def __str__(self):
        return f'Sessão {self.pk} — {self.inicio:%d/%m/%Y %H:%M}'
