from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.models import Usuario


class UsuarioAdminFormTests(TestCase):
    """O Admin cria a conta e o perfil GAAP juntos, com papéis sem ambiguidade."""

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username='admin-form-test',
            email='admin-form@example.com',
            password='Coord!AdminForm-2026',
        )
        self.client.force_login(self.admin)
        self.add_url = reverse('admin:app_usuario_add')

    def dados(self, **sobrescritas):
        dados = {
            'login': 'marina-professora',
            'senha': 'S0m3-Long!Passphrase-2026',
            'nome': 'Marina Costa',
            'email': 'marina@example.com',
            'telefone': '',
            'perfil': Usuario.Perfil.TREINADOR,
            '_save': 'Salvar',
        }
        dados.update(sobrescritas)
        return dados

    def test_formulario_cria_conta_e_perfil_e_explica_os_papeis(self):
        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="login"')
        self.assertContains(response, 'name="senha"')
        self.assertNotContains(response, 'name="conta"')
        self.assertContains(response, 'Coordenador (acesso administrativo)')
        self.assertContains(response, 'Professor/Treinador')
        self.assertContains(response, 'Somente o coordenador deve receber acesso administrativo.')

        response = self.client.post(self.add_url, self.dados())

        self.assertEqual(response.status_code, 302)
        conta = get_user_model().objects.get(username='marina-professora')
        perfil = Usuario.objects.get(conta=conta)
        self.assertEqual(perfil.perfil, Usuario.Perfil.TREINADOR)
        self.assertTrue(conta.check_password('S0m3-Long!Passphrase-2026'))
        self.assertFalse(conta.is_superuser)

    def test_perfil_coordenador_nao_cria_superusuario_tecnico(self):
        dados = self.dados(
            login='coordenadora-gaap',
            senha='S0m3-Long!Coordinator-2026',
            nome='Coordenadora GAAP',
            email='coordenadora@example.com',
            perfil=Usuario.Perfil.ADMINISTRADOR,
        )

        response = self.client.post(self.add_url, dados)

        self.assertEqual(response.status_code, 302)
        conta = get_user_model().objects.get(username='coordenadora-gaap')
        perfil = Usuario.objects.get(conta=conta)
        self.assertEqual(perfil.perfil, Usuario.Perfil.ADMINISTRADOR)
        self.assertFalse(conta.is_superuser)

    def test_login_duplicado_e_recusado(self):
        response = self.client.post(self.add_url, self.dados(login=self.admin.username))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Já existe uma conta com este login.')
        self.assertFalse(Usuario.objects.filter(email='marina@example.com').exists())

    def test_edicao_sem_nova_senha_preserva_a_senha_atual(self):
        conta = get_user_model().objects.create_user(
            username='marina-antiga',
            email='marina-antiga@example.com',
            password='Existing!ProfilePass-2026',
        )
        perfil = Usuario.objects.create(
            conta=conta,
            nome='Marina Costa',
            email='marina-antiga@example.com',
            perfil=Usuario.Perfil.TREINADOR,
        )
        url = reverse('admin:app_usuario_change', args=[perfil.pk])

        response = self.client.post(
            url,
            {
                'login': 'marina-nova',
                'senha': '',
                'nome': 'Marina Costa',
                'email': 'marina-nova@example.com',
                'telefone': '',
                'perfil': Usuario.Perfil.TREINADOR,
                '_save': 'Salvar',
            },
        )

        self.assertEqual(response.status_code, 302)
        conta.refresh_from_db()
        perfil.refresh_from_db()
        self.assertEqual(conta.username, 'marina-nova')
        self.assertEqual(conta.email, 'marina-nova@example.com')
        self.assertEqual(perfil.email, 'marina-nova@example.com')
        self.assertTrue(conta.check_password('Existing!ProfilePass-2026'))
