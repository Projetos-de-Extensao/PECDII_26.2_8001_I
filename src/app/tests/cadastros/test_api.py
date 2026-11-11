from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import Aluno, Sessao, Servico, Usuario
from app.tests.helpers import cliente_autenticado


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TelefoneApiTests(TestCase):
    """Verifica a validação e normalização de telefones pela API."""

    def setUp(self):
        self.client = cliente_autenticado(
            Usuario.Perfil.ADMINISTRADOR, 'teste-api-aluno'
        )

    def test_aluno_telefone_sem_mascara_e_normalizado(self):
        response = self.client.post(
            '/api/alunos/',
            {
                'nome': 'Ana Silva',
                'data_nascimento': '2000-01-01',
                'telefone': '11987654321',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['telefone'], '+55 11 98765-4321')

    def test_profissional_telefone_com_ddi_e_mascara_e_normalizado(self):
        response = self.client.post(
            '/api/profissionais/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'telefone': '+55 21 91234-5678',
                'perfil': Usuario.Perfil.TREINADOR,
                'login': 'bruno-costa',
                'senha': 'SenhaForte2026',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['telefone'], '+55 21 91234-5678')

    def test_telefone_com_ddi_americano_preserva_o_pais(self):
        response = self.client.post(
            '/api/alunos/',
            {
                'nome': 'Chris Smith',
                'data_nascimento': '2000-01-01',
                'telefone': '+1 650-253-0000',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['telefone'], '+1 650-253-0000')
        self.assertEqual(Aluno.objects.get(nome='Chris Smith').telefone, '+16502530000')

    def test_telefone_com_quantidade_de_digitos_invalida_e_rejeitado(self):
        response = self.client.post(
            '/api/alunos/',
            {
                'nome': 'Ana Silva',
                'data_nascimento': '2000-01-01',
                'telefone': '1198765432',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('telefone', response.data)
        self.assertFalse(Aluno.objects.exists())


class AutenticacaoApiTests(TestCase):
    """Verifica que a API só responde a requisições autenticadas."""

    def setUp(self):
        self.client = APIClient()

    def test_consulta_sem_autenticacao_e_recusada(self):
        rotas = ('/api/alunos/', '/api/profissionais/', '/api/servicos/', '/api/sessoes/')
        for rota in rotas:
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 401)

    def test_cadastro_sem_autenticacao_e_recusado(self):
        response = self.client.post(
            '/api/alunos/',
            {'nome': 'Ana Silva', 'data_nascimento': '2000-01-01'},
            format='json',
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Aluno.objects.exists())


class PermissaoCadastroTests(TestCase):
    """Verifica o que cada perfil pode fazer nos cadastros da API."""

    def setUp(self):
        self.aluno = Aluno.objects.create(nome='Ana Silva', data_nascimento='2000-01-01')
        self.servico = Servico.objects.create(
            nome='Treino funcional',
            categoria=Servico.Categoria.TREINO,
        )

    def test_administrador_cria_consulta_e_atualiza_cadastros(self):
        client = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-cadastro')

        criado = client.post(
            '/api/alunos/',
            {'nome': 'Carla Dias', 'data_nascimento': '1999-05-10'},
            format='json',
        )
        consulta = client.get('/api/alunos/')
        atualizado = client.patch(
            f'/api/alunos/{self.aluno.pk}/',
            {'nome': 'Ana Silva Souza'},
            format='json',
        )

        self.assertEqual(criado.status_code, 201)
        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(atualizado.status_code, 200)

    def test_administrador_cria_servico_e_profissional(self):
        client = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-servico')

        servico = client.post(
            '/api/servicos/',
            {'nome': 'Fisioterapia esportiva', 'categoria': Servico.Categoria.FISIOTERAPIA},
            format='json',
        )
        profissional = client.post(
            '/api/profissionais/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'perfil': Usuario.Perfil.TREINADOR,
                'login': 'bruno',
                'senha': 'SenhaForte2026',
            },
            format='json',
        )

        self.assertEqual(servico.status_code, 201)
        self.assertEqual(profissional.status_code, 201)

    def test_treinador_consulta_mas_nao_administra_cadastros(self):
        client = cliente_autenticado(Usuario.Perfil.TREINADOR, 'treinador-cadastro')

        consulta = client.get('/api/alunos/')
        criacao = client.post(
            '/api/alunos/',
            {'nome': 'Carla Dias', 'data_nascimento': '1999-05-10'},
            format='json',
        )
        atualizacao = client.patch(
            f'/api/alunos/{self.aluno.pk}/',
            {'nome': 'Ana Silva Souza'},
            format='json',
        )
        exclusao = client.delete(f'/api/alunos/{self.aluno.pk}/')

        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(criacao.status_code, 403)
        self.assertEqual(atualizacao.status_code, 403)
        self.assertEqual(exclusao.status_code, 403)
        self.assertEqual(Aluno.objects.count(), 1)

    def test_profissional_de_saude_nao_administra_servicos_nem_profissionais(self):
        client = cliente_autenticado(Usuario.Perfil.PROFISSIONAL_SAUDE, 'saude-cadastro')

        servico = client.post(
            '/api/servicos/',
            {'nome': 'Psicologia do esporte', 'categoria': Servico.Categoria.PSICOLOGIA},
            format='json',
        )
        profissional = client.post(
            '/api/profissionais/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'perfil': Usuario.Perfil.TREINADOR,
                'login': 'bruno',
                'senha': 'SenhaForte2026',
            },
            format='json',
        )
        atualizacao = client.patch(
            f'/api/servicos/{self.servico.pk}/',
            {'nome': 'Treino de força'},
            format='json',
        )

        self.assertEqual(servico.status_code, 403)
        self.assertEqual(profissional.status_code, 403)
        self.assertEqual(atualizacao.status_code, 403)
        self.assertEqual(Servico.objects.count(), 1)

    def test_superusuario_administra_cadastros(self):
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.create_superuser(username='root')
        )

        response = client.post(
            '/api/servicos/',
            {'nome': 'Nutrição esportiva', 'categoria': Servico.Categoria.NUTRICAO},
            format='json',
        )

        self.assertEqual(response.status_code, 201)

    def test_conta_sem_perfil_consulta_mas_nao_administra(self):
        client = APIClient()
        client.force_authenticate(
            user=get_user_model().objects.create_user(username='sem-perfil')
        )

        consulta = client.get('/api/alunos/')
        criacao = client.post(
            '/api/alunos/',
            {'nome': 'Carla Dias', 'data_nascimento': '1999-05-10'},
            format='json',
        )

        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(criacao.status_code, 403)
        self.assertEqual(Aluno.objects.count(), 1)

    def test_treinador_nao_administra_profissionais(self):
        client = cliente_autenticado(Usuario.Perfil.TREINADOR, 'treinador-professor')

        response = client.post(
            '/api/profissionais/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'perfil': Usuario.Perfil.TREINADOR,
                'login': 'bruno-costa',
                'senha': 'SenhaForte2026',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Usuario.objects.filter(email='bruno@example.com').exists())


class ProfissionalApiTests(TestCase):
    """Verifica o cadastro de profissionais e a conta de acesso criada."""

    def setUp(self):
        self.client = cliente_autenticado(
            Usuario.Perfil.ADMINISTRADOR, 'admin-profissional'
        )

    def cadastrar(self, **overrides):
        dados = {
            'nome': 'Bruno Costa',
            'email': 'bruno@example.com',
            'perfil': Usuario.Perfil.TREINADOR,
            'login': 'bruno',
            'senha': 'SenhaForte2026',
        }
        dados.update(overrides)
        return self.client.post('/api/profissionais/', dados, format='json')

    def test_cadastro_guarda_a_senha_somente_como_hash(self):
        response = self.cadastrar()

        conta = Usuario.objects.get(email='bruno@example.com').conta
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('senha', response.data)
        self.assertNotEqual(conta.password, 'SenhaForte2026')
        self.assertTrue(conta.check_password('SenhaForte2026'))

    def test_cadastro_sem_login_e_senha_e_rejeitado(self):
        response = self.client.post(
            '/api/profissionais/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'perfil': Usuario.Perfil.TREINADOR,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('login', response.data)
        self.assertIn('senha', response.data)

    def test_login_repetido_e_rejeitado(self):
        self.cadastrar()

        response = self.cadastrar(email='outro@example.com')

        self.assertEqual(response.status_code, 400)
        self.assertIn('login', response.data)

    def test_perfil_administrador_nao_e_aceito_no_cadastro_de_profissionais(self):
        response = self.cadastrar(perfil=Usuario.Perfil.ADMINISTRADOR)

        self.assertEqual(response.status_code, 400)
        self.assertIn('perfil', response.data)

    def test_remocao_encerra_a_conta_de_acesso(self):
        self.cadastrar()
        profissional = Usuario.objects.get(email='bruno@example.com')

        response = self.client.delete(f'/api/profissionais/{profissional.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Usuario.objects.filter(pk=profissional.pk).exists())
        self.assertFalse(get_user_model().objects.filter(username='bruno').exists())

    def test_remocao_de_profissional_com_sessoes_e_recusada(self):
        self.cadastrar()
        profissional = Usuario.objects.get(email='bruno@example.com')
        agora = timezone.now()
        Sessao.objects.create(inicio=agora, fim=agora + timedelta(hours=1), profissional=profissional)

        response = self.client.delete(f'/api/profissionais/{profissional.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertIn('Transfira as sessões', response.data['detail'])
        self.assertTrue(Usuario.objects.filter(pk=profissional.pk).exists())
        self.assertTrue(get_user_model().objects.filter(username='bruno').exists())

    def test_listagem_traz_apenas_perfis_profissionais(self):
        self.cadastrar()

        response = self.client.get('/api/profissionais/')

        perfis = [item['perfil'] for item in response.data]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(perfis, [Usuario.Perfil.TREINADOR])


class ServicoApiTests(TestCase):
    """Verifica as categorias e a unicidade do nome dos serviços."""

    def setUp(self):
        self.client = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-catalogo')

    def test_cria_servico_em_cada_categoria(self):
        for categoria in Servico.Categoria.values:
            with self.subTest(categoria=categoria):
                response = self.client.post(
                    '/api/servicos/',
                    {'nome': f'Serviço {categoria}', 'categoria': categoria},
                    format='json',
                )
                self.assertEqual(response.status_code, 201)

        self.assertEqual(Servico.objects.count(), len(Servico.Categoria.values))

    def test_nome_repetido_e_rejeitado(self):
        Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)

        response = self.client.post(
            '/api/servicos/',
            {'nome': 'Treino funcional', 'categoria': Servico.Categoria.TREINO},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('nome', response.data)

    def test_categoria_fora_da_lista_e_rejeitada(self):
        response = self.client.post(
            '/api/servicos/',
            {'nome': 'Acupuntura', 'categoria': 'ACUPUNTURA'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('categoria', response.data)
