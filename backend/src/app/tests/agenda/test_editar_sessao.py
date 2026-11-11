from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from app.models import Aluno, Disponibilidade, Participacao, ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_para, criar_perfil


class EdicaoDeAgendaDaSessaoTests(TestCase):
    """Edições administrativas revalidam as regras da agenda antes de gravar."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-editar-sessao')
        self.client = cliente_para(self.admin)
        self.profissional = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-editar-sessao')
        self.outro = criar_perfil(Usuario.Perfil.TREINADOR, 'outro-editar-sessao')
        self.servico = Servico.objects.create(
            nome='Treino de força', categoria=Servico.Categoria.TREINO,
        )
        self.outro_servico = Servico.objects.create(
            nome='Treino de mobilidade', categoria=Servico.Categoria.TREINO,
        )
        ProfissionalServico.objects.create(profissional=self.profissional, servico=self.servico)
        self.base = (timezone.now() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
        Disponibilidade.objects.create(
            profissional=self.profissional,
            inicio=self.base - timedelta(hours=2),
            fim=self.base + timedelta(hours=6),
        )
        self.aluno = Aluno.objects.create(nome='Ana Lima', data_nascimento='2010-03-01')
        self.sessao = Sessao.objects.create(
            titulo='Sessão da manhã',
            servico=self.servico,
            profissional=self.profissional,
            inicio=self.base,
            fim=self.base + timedelta(hours=1),
        )
        Participacao.objects.create(sessao=self.sessao, aluno=self.aluno)

    def patch_agenda(self, inicio, fim, **extra):
        return self.client.patch(
            f'/api/sessoes/{self.sessao.pk}/',
            {'inicio': inicio.isoformat(), 'fim': fim.isoformat(), **extra},
            format='json',
        )

    def test_editar_horario_rejeita_conflito_do_profissional(self):
        conflito_inicio = self.base + timedelta(hours=2)
        Sessao.objects.create(
            titulo='Outro compromisso',
            servico=self.servico,
            profissional=self.profissional,
            inicio=conflito_inicio,
            fim=conflito_inicio + timedelta(hours=1),
        )

        response = self.patch_agenda(conflito_inicio, conflito_inicio + timedelta(hours=1))

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-01')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.inicio, self.base)

    def test_editar_horario_rejeita_fora_da_disponibilidade(self):
        inicio = self.base + timedelta(days=1)

        response = self.patch_agenda(inicio, inicio + timedelta(hours=1))

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-03')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.inicio, self.base)

    def test_editar_servico_rejeita_profissional_sem_habilitacao(self):
        response = self.client.patch(
            f'/api/sessoes/{self.sessao.pk}/',
            {'servico': self.outro_servico.pk},
            format='json',
        )

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-04')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.servico, self.servico)

    def test_editar_profissional_rejeita_profissional_sem_habilitacao(self):
        response = self.client.patch(
            f'/api/sessoes/{self.sessao.pk}/',
            {'profissional': self.outro.pk},
            format='json',
        )

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-04')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.profissional, self.profissional)

    def test_editar_horario_rejeita_conflito_do_aluno(self):
        conflito_inicio = self.base + timedelta(hours=2)
        outra = Sessao.objects.create(
            titulo='Atendimento do aluno',
            servico=self.servico,
            profissional=self.outro,
            inicio=conflito_inicio,
            fim=conflito_inicio + timedelta(hours=1),
        )
        Participacao.objects.create(sessao=outra, aluno=self.aluno)

        response = self.patch_agenda(conflito_inicio, conflito_inicio + timedelta(hours=1))

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-07')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.inicio, self.base)

    def test_editar_horario_valido_nao_conflita_com_a_propria_sessao(self):
        novo_inicio = self.base + timedelta(hours=2)
        response = self.patch_agenda(novo_inicio, novo_inicio + timedelta(hours=1))

        self.assertEqual(response.status_code, 200, response.data)
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.inicio, novo_inicio)

    def test_reativar_sessao_cancelada_revalida_disponibilidade(self):
        self.sessao.status = Sessao.Status.CANCELADA
        self.sessao.save()
        Disponibilidade.objects.filter(profissional=self.profissional).delete()

        response = self.client.patch(
            f'/api/sessoes/{self.sessao.pk}/',
            {'status': Sessao.Status.AGENDADA},
            format='json',
        )

        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(response.data['regra'], 'RN-03')
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.status, Sessao.Status.CANCELADA)
