from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from app.models import Aluno, Disponibilidade, ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_para, criar_perfil


class StatusDeAtendimentoProfissionalSaudeTests(TestCase):
    """Profissionais de saúde responsáveis também registram o desfecho (RF-10)."""

    def setUp(self):
        self.fisio = criar_perfil(Usuario.Perfil.PROFISSIONAL_SAUDE, 'fisio-status-sessao')
        self.client = cliente_para(self.fisio)
        self.servico = Servico.objects.create(
            nome='Fisioterapia esportiva', categoria=Servico.Categoria.FISIOTERAPIA,
        )
        ProfissionalServico.objects.create(profissional=self.fisio, servico=self.servico)
        agora = timezone.now()
        Disponibilidade.objects.create(
            profissional=self.fisio,
            inicio=agora - timedelta(days=1),
            fim=agora + timedelta(days=1),
        )
        self.sessao = Sessao.objects.create(
            titulo='Atendimento de fisioterapia',
            servico=self.servico,
            profissional=self.fisio,
            inicio=agora - timedelta(hours=2),
            fim=agora - timedelta(hours=1),
        )
        self.aluno = Aluno.objects.create(nome='Ana Lima', data_nascimento='2010-03-01')
        self.sessao.participacoes.create(aluno=self.aluno)

    def test_profissional_de_saude_registra_sessao_realizada(self):
        response = self.client.patch(
            f'/api/sessoes/{self.sessao.pk}/',
            {'status': Sessao.Status.REALIZADA},
            format='json',
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.status, Sessao.Status.REALIZADA)
