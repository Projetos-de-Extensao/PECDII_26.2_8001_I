import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from app.models import ProfissionalServico, Servico, Usuario


class AutenticacaoClienteWebTests(TestCase):
    """Login por sessão, CSRF e exposição mínima do perfil para o cliente web."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.conta = get_user_model().objects.create_user(
            username='treinador-web',
            email='treinador@example.com',
            password='SenhaSegura#2026',
        )
        self.usuario = Usuario.objects.create(
            conta=self.conta,
            nome='Treinador Web',
            email='treinador@example.com',
            perfil=Usuario.Perfil.TREINADOR,
        )
        self.servico = Servico.objects.create(nome='Treino web', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.usuario, servico=self.servico)

    def obter_token_csrf(self):
        response = self.client.get('/api/auth/csrf/')
        self.assertEqual(response.status_code, 200)
        return response.json()['csrfToken']

    def post_json_com_csrf(self, url, dados):
        return self.client.post(
            url,
            data=json.dumps(dados),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.obter_token_csrf(),
        )

    def test_login_por_email_cria_sessao_e_retorna_perfil_e_servicos(self):
        response = self.post_json_com_csrf(
            '/api/auth/login/', {'login': 'treinador@example.com', 'senha': 'SenhaSegura#2026'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['perfil'], Usuario.Perfil.TREINADOR)
        self.assertEqual(response.json()['id'], self.usuario.pk)
        self.assertEqual(response.json()['servicos'], [
            {'id': self.servico.pk, 'nome': 'Treino web', 'categoria': Servico.Categoria.TREINO},
        ])
        self.assertNotIn('senha', response.json())
        sessao = self.client.get('/api/auth/session/')
        self.assertEqual(sessao.status_code, 200)
        self.assertEqual(sessao.json()['email'], 'treinador@example.com')

    def test_login_por_nome_de_usuario_e_suportado(self):
        response = self.post_json_com_csrf(
            '/api/auth/login/', {'login': 'treinador-web', 'senha': 'SenhaSegura#2026'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.usuario.pk)

    def test_login_sem_csrf_e_recusado(self):
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({'login': 'treinador-web', 'senha': 'SenhaSegura#2026'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_credenciais_invalidas_nao_criam_sessao(self):
        response = self.post_json_com_csrf('/api/auth/login/', {'login': 'treinador-web', 'senha': 'errada'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.get('/api/auth/session/').status_code, 401)

    def test_logout_exige_csrf_e_encerra_a_sessao(self):
        self.post_json_com_csrf(
            '/api/auth/login/', {'login': 'treinador-web', 'senha': 'SenhaSegura#2026'}
        )

        resposta_logout = self.client.post(
            '/api/auth/logout/',
            data='{}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value,
        )

        self.assertEqual(resposta_logout.status_code, 200)
        self.assertEqual(self.client.get('/api/auth/session/').status_code, 401)

    def test_conta_sem_perfil_gaap_nao_recebe_sessao(self):
        conta = get_user_model().objects.create_user(username='sem-perfil', password='SenhaSegura#2026')
        self.assertTrue(conta.check_password('SenhaSegura#2026'))

        response = self.post_json_com_csrf(
            '/api/auth/login/', {'login': 'sem-perfil', 'senha': 'SenhaSegura#2026'}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.get('/api/auth/session/').status_code, 401)

