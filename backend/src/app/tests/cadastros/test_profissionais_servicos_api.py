from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from app.models import ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_autenticado


class ProfissionalServicoApiTests(TestCase):
    """Verifica o cadastro de habilitações usadas pelo RN-04."""

    def setUp(self):
        self.admin_client = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-habilitacoes')
        self.profissional_client = cliente_autenticado(Usuario.Perfil.TREINADOR, 'treinador-habilitacoes')
        self.profissional = Usuario.objects.get(email='treinador-habilitacoes@example.com')
        self.servico = Servico.objects.create(
            nome='Treino de força', categoria=Servico.Categoria.TREINO,
        )

    def test_lista_habilitacoes_e_profissionais_no_servico(self):
        vinculo = ProfissionalServico.objects.create(
            profissional=self.profissional, servico=self.servico,
        )

        resposta_vinculos = self.profissional_client.get('/api/profissionais-servicos/')
        resposta_servicos = self.profissional_client.get('/api/servicos/')

        self.assertEqual(resposta_vinculos.status_code, 200)
        self.assertEqual(resposta_vinculos.data, [{
            'id': vinculo.pk,
            'profissional': self.profissional.pk,
            'servico': self.servico.pk,
        }])
        self.assertEqual(resposta_servicos.data[0]['profissionais_habilitados'], [self.profissional.pk])

    def test_administrador_cria_habilitacao(self):
        resposta = self.admin_client.post(
            '/api/profissionais-servicos/',
            {'profissional': self.profissional.pk, 'servico': self.servico.pk},
            format='json',
        )

        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(ProfissionalServico.objects.count(), 1)

    def test_profissional_nao_pode_alterar_habilitacoes(self):
        resposta = self.profissional_client.post(
            '/api/profissionais-servicos/',
            {'profissional': self.profissional.pk, 'servico': self.servico.pk},
            format='json',
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(ProfissionalServico.objects.exists())

    def test_habilitacao_duplicada_tem_erro_de_validacao(self):
        ProfissionalServico.objects.create(profissional=self.profissional, servico=self.servico)

        resposta = self.admin_client.post(
            '/api/profissionais-servicos/',
            {'profissional': self.profissional.pk, 'servico': self.servico.pk},
            format='json',
        )

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(ProfissionalServico.objects.count(), 1)

    def test_nao_remove_habilitacao_com_sessao_futura(self):
        vinculo = ProfissionalServico.objects.create(
            profissional=self.profissional, servico=self.servico,
        )
        inicio = timezone.now() + timedelta(hours=1)
        Sessao.objects.create(
            inicio=inicio,
            fim=inicio + timedelta(minutes=30),
            servico=self.servico,
            profissional=self.profissional,
        )

        resposta = self.admin_client.delete(f'/api/profissionais-servicos/{vinculo.pk}/')

        self.assertEqual(resposta.status_code, 409)
        self.assertTrue(ProfissionalServico.objects.filter(pk=vinculo.pk).exists())

    def test_sessao_cancelada_nao_impede_remover_habilitacao(self):
        vinculo = ProfissionalServico.objects.create(
            profissional=self.profissional, servico=self.servico,
        )
        inicio = timezone.now() + timedelta(hours=1)
        Sessao.objects.create(
            inicio=inicio,
            fim=inicio + timedelta(minutes=30),
            servico=self.servico,
            profissional=self.profissional,
            status=Sessao.Status.CANCELADA,
        )

        resposta = self.admin_client.delete(f'/api/profissionais-servicos/{vinculo.pk}/')

        self.assertEqual(resposta.status_code, 204)
        self.assertFalse(ProfissionalServico.objects.filter(pk=vinculo.pk).exists())
