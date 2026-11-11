from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase

from app.models import (
    Disponibilidade,
    ProfissionalServico,
    RegistroAuditoria,
    Servico,
    Sessao,
    Usuario,
)
from app.tests.agenda.test_confirmacao import INICIO, criar_alunos
from app.tests.helpers import cliente_para as cliente, criar_perfil
from app.tests.sessoes.test_presenca import BaseSessaoTests

Operacao = RegistroAuditoria.Operacao
SENHA = 'SenhaMuitoForte!2026'


def campos_de_texto(registro):
    """Junta todos os textos gravados num registro, para procurar segredos."""
    return ' '.join(str(valor) for valor in (registro.autor, registro.mensagem, registro.entidade))


class AuditoriaCriacaoUsuarioTests(TestCase):
    """Criação de usuário pela API e pelo Django Admin."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-auditoria', nome='Carla Admin')

    def test_api_registra_criacao_com_autor_entidade_e_mensagem(self):
        response = cliente(self.admin).post('/api/profissionais/', {
            'nome': 'Diego Treinador',
            'email': 'diego@example.com',
            'perfil': Usuario.Perfil.TREINADOR,
            'login': 'diego',
            'senha': SENHA,
        }, format='json')
        self.assertEqual(response.status_code, 201)

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.operacao, Operacao.USUARIO_CRIADO)
        self.assertEqual(registro.usuario, self.admin)
        self.assertEqual(registro.autor, 'Carla Admin')
        self.assertEqual(registro.entidade, 'Usuario')
        self.assertEqual(registro.entidade_id, response.data['id'])
        self.assertIsNotNone(registro.registrado_em)
        self.assertEqual(
            registro.mensagem,
            'Carla Admin criou o usuário "Diego Treinador" com o perfil Treinador.',
        )

    def test_api_nao_registra_senha_nem_hash(self):
        cliente(self.admin).post('/api/profissionais/', {
            'nome': 'Diego Treinador',
            'email': 'diego@example.com',
            'perfil': Usuario.Perfil.TREINADOR,
            'login': 'diego',
            'senha': SENHA,
        }, format='json')

        texto = campos_de_texto(RegistroAuditoria.objects.get())
        hash_da_senha = get_user_model().objects.get(username='diego').password
        self.assertNotIn(SENHA, texto)
        self.assertNotIn(hash_da_senha, texto)

    def test_cadastro_invalido_nao_gera_registro(self):
        response = cliente(self.admin).post('/api/profissionais/', {'nome': 'Sem dados'}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RegistroAuditoria.objects.exists())

    def test_django_admin_registra_criacao_sem_senha(self):
        superusuario = get_user_model().objects.create_superuser('coordenacao', password='x')
        navegador = Client()
        navegador.force_login(superusuario)

        response = navegador.post('/admin/app/usuario/add/', {
            'login': 'eva',
            'senha': SENHA,
            'nome': 'Eva Fisio',
            'email': 'eva@example.com',
            'telefone': '',
            'perfil': Usuario.Perfil.PROFISSIONAL_SAUDE,
        })
        self.assertEqual(response.status_code, 302)

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.operacao, Operacao.USUARIO_CRIADO)
        self.assertIsNone(registro.usuario)  # superusuário sem perfil GAAP
        self.assertEqual(registro.autor, 'coordenacao')
        self.assertNotIn(SENHA, campos_de_texto(registro))


class AuditoriaConfirmacaoTests(TestCase):
    """Confirmação de agendamento (UC-05)."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-agenda', nome='Carla Admin')
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-agenda', nome='Diego')
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=INICIO - timedelta(days=1),
            fim=INICIO + timedelta(days=1),
        )
        self.alunos = criar_alunos(7)

    def dados(self, quantidade_de_alunos):
        return {
            'titulo': 'Treino de força',
            'tipo': Sessao.Tipo.TREINAMENTO,
            'inicio': INICIO.isoformat(),
            'fim': (INICIO + timedelta(hours=1)).isoformat(),
            'servico': self.servico.pk,
            'profissional': self.treinador.pk,
            'participantes': [aluno.pk for aluno in self.alunos[:quantidade_de_alunos]],
        }

    def test_registra_confirmacao_de_agendamento(self):
        response = cliente(self.admin).post('/api/sessoes/', self.dados(2), format='json')
        self.assertEqual(response.status_code, 201)

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.operacao, Operacao.AGENDAMENTO_CONFIRMADO)
        self.assertEqual(registro.usuario, self.admin)
        self.assertEqual(registro.entidade, 'Sessao')
        self.assertEqual(registro.entidade_id, response.data['id'])
        self.assertIn('confirmou o agendamento "Treino de força"', registro.mensagem)
        self.assertIn('2 aluno(s)', registro.mensagem)

    def test_agendamento_recusado_nao_gera_registro(self):
        response = cliente(self.admin).post('/api/sessoes/', self.dados(7), format='json')  # acima de 6 alunos

        self.assertEqual(response.status_code, 409)
        self.assertFalse(RegistroAuditoria.objects.exists())


class AuditoriaPresencaERelatorioTests(BaseSessaoTests):
    """Alteração de presença/falta (RF-06) e finalização do relatório (RF-07)."""

    def test_registra_alteracao_de_presenca_com_nomes(self):
        response = cliente(self.responsavel).patch(self.url_presencas, {'presencas': [
            {'aluno': self.ana.pk, 'situacao': 'PRESENTE'},
            {'aluno': self.bruno.pk, 'situacao': 'FALTA'},
        ]}, format='json')
        self.assertEqual(response.status_code, 200)

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.operacao, Operacao.PRESENCA_ALTERADA)
        self.assertEqual(registro.usuario, self.responsavel)
        self.assertEqual(registro.entidade, 'Sessao')
        self.assertEqual(registro.entidade_id, self.sessao.pk)
        self.assertIn('Ana Lima: presente', registro.mensagem)
        self.assertIn('Bruno Costa: falta', registro.mensagem)

    def test_repetir_a_mesma_presenca_nao_gera_novo_registro(self):
        dados = {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}
        cliente(self.responsavel).patch(self.url_presencas, dados, format='json')
        cliente(self.responsavel).patch(self.url_presencas, dados, format='json')

        self.assertEqual(RegistroAuditoria.objects.count(), 1)

    def test_registra_finalizacao_do_relatorio(self):
        self.sessao.status = Sessao.Status.REALIZADA
        self.sessao.save()
        url = f'/api/sessoes/{self.sessao.pk}/relatorio/'
        cliente(self.responsavel).post(url, {'objetivo': 'Força'}, format='json')
        response = cliente(self.responsavel).post(f'{url}finalizar/', {
            'data': '2026-11-16', 'horario': '10:00:00', 'local': 'Sala 2', 'exercicios': 'Agachamento',
            'volume_valor': '100', 'volume_unidade': 'kg', 'intensidade_borg': '6',
        }, format='json')
        self.assertEqual(response.status_code, 200)

        registro = RegistroAuditoria.objects.get()
        self.assertEqual(registro.operacao, Operacao.RELATORIO_FINALIZADO)
        self.assertEqual(registro.entidade, 'RelatorioTreino')
        self.assertEqual(registro.entidade_id, response.data['id'])
        self.assertEqual(
            registro.mensagem,
            'treinador-responsavel finalizou o relatório de treino da sessão "Treino de força".',
        )


class AuditoriaImutavelTests(TestCase):
    """A API só consulta; ninguém altera ou apaga registros."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-consulta')
        self.registro = RegistroAuditoria.objects.create(
            usuario=self.admin,
            autor='admin-consulta',
            operacao=Operacao.USUARIO_CRIADO,
            entidade='Usuario',
            entidade_id=self.admin.pk,
            mensagem='admin-consulta criou o usuário "Teste".',
        )
        self.url = f'/api/auditoria/{self.registro.pk}/'

    def test_administrador_consulta_e_filtra_registros(self):
        client = cliente(self.admin)

        todos = client.get('/api/auditoria/')
        filtrados = client.get('/api/auditoria/', {'operacao': Operacao.RELATORIO_FINALIZADO})

        self.assertEqual(todos.status_code, 200)
        self.assertEqual(todos.data[0]['operacao_rotulo'], 'Criação de usuário')
        self.assertEqual(filtrados.data, [])

    def test_filtro_por_entidade(self):
        client = cliente(self.admin)

        encontrado = client.get('/api/auditoria/', {'entidade': 'Usuario', 'entidade_id': self.admin.pk})
        invalido = client.get('/api/auditoria/', {'entidade_id': 'abc'})

        self.assertEqual(len(encontrado.data), 1)
        self.assertEqual(invalido.status_code, 400)

    def test_outros_perfis_nao_consultam(self):
        treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-curioso')

        response = cliente(treinador).get('/api/auditoria/')

        self.assertEqual(response.status_code, 403)

    def test_api_nao_cria_altera_nem_apaga(self):
        client = cliente(self.admin)

        respostas = [
            client.post('/api/auditoria/', {'mensagem': 'falso'}, format='json'),
            client.put(self.url, {'mensagem': 'alterado'}, format='json'),
            client.patch(self.url, {'mensagem': 'alterado'}, format='json'),
            client.delete(self.url),
        ]

        self.assertEqual([r.status_code for r in respostas], [405, 405, 405, 405])
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.mensagem, 'admin-consulta criou o usuário "Teste".')

    def test_modelo_recusa_alteracao_e_exclusao(self):
        self.registro.mensagem = 'alterado'
        with self.assertRaises(ValidationError):
            self.registro.save()
        with self.assertRaises(ValidationError):
            self.registro.delete()
        self.assertTrue(RegistroAuditoria.objects.filter(pk=self.registro.pk).exists())
