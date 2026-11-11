from datetime import timedelta

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class MigrarProfessorParaUsuarioTests(TransactionTestCase):
    """Confere a migração de dados da Construção 1 com o schema histórico."""

    migrate_from = [('app', '0011_profissional_servico')]
    migrate_to = [('app', '0012_migrar_professor_para_usuario')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        apps_anteriores = executor.loader.project_state(self.migrate_from).apps

        ProfessorAntigo = apps_anteriores.get_model('app', 'Professor')
        SessaoAntiga = apps_anteriores.get_model('app', 'Sessao')
        professor = ProfessorAntigo.objects.create(
            nome='Bruno Costa',
            email='bruno-legado@example.com',
            telefone='+5521912345678',
        )
        sessao = SessaoAntiga.objects.create(
            titulo='Treino legado',
            tipo='TREINAMENTO',
            inicio=timezone.now() + timedelta(days=1),
            fim=timezone.now() + timedelta(days=1, minutes=60),
            professor_id=professor.pk,
        )
        self.professor_id = professor.pk
        self.sessao_id = sessao.pk

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps_migradas = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        # A sessão legada não tem serviço, e a 0015 recusa sessões assim; ela sai antes de
        # voltar o schema para a última migração.
        self.apps_migradas.get_model('app', 'Sessao').objects.all().delete()
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_mantem_contato_e_sessao_e_cria_treinador_sem_senha_utilizavel(self):
        UsuarioMigrado = self.apps_migradas.get_model('app', 'Usuario')
        SessaoMigrada = self.apps_migradas.get_model('app', 'Sessao')
        perfil = UsuarioMigrado.objects.get(email='bruno-legado@example.com')
        sessao = SessaoMigrada.objects.get(pk=self.sessao_id)

        self.assertEqual(perfil.nome, 'Bruno Costa')
        self.assertEqual(perfil.telefone, '+5521912345678')
        self.assertEqual(perfil.perfil, 'TREINADOR')
        self.assertEqual(perfil.conta.username, f'gaap-migrado-professor-{self.professor_id}')
        self.assertTrue(perfil.conta.password.startswith('!'))
        self.assertEqual(sessao.profissional_id, perfil.pk)


class SessaoComServicoEProfissionalObrigatoriosTests(TransactionTestCase):
    """A 0015 só torna as colunas obrigatórias se não houver sessão incompleta."""

    migrate_from = [('app', '0014_participacao_servico_da_sessao')]
    migrate_to = [('app', '0015_servico_profissional_obrigatorios')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.apps_anteriores = executor.loader.project_state(self.migrate_from).apps

        Usuario = self.apps_anteriores.get_model('app', 'Usuario')
        Conta = self.apps_anteriores.get_model('auth', 'User')
        Servico = self.apps_anteriores.get_model('app', 'Servico')
        conta = Conta.objects.create(username='treinador-0015')
        self.treinador = Usuario.objects.create(
            conta=conta, nome='Treinador 0015', email='treinador-0015@example.com', perfil='TREINADOR'
        )
        self.servico = Servico.objects.create(nome='Treino 0015', categoria='TREINO')

    def tearDown(self):
        self.apps_anteriores.get_model('app', 'Sessao').objects.all().delete()
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def criar_sessao(self, **campos):
        Sessao = self.apps_anteriores.get_model('app', 'Sessao')
        inicio = timezone.now() + timedelta(days=1)
        return Sessao.objects.create(
            titulo='Sessão 0015', tipo='TREINAMENTO', inicio=inicio, fim=inicio + timedelta(hours=1), **campos
        )

    def test_migra_quando_todas_as_sessoes_estao_completas(self):
        sessao = self.criar_sessao(servico_id=self.servico.pk, profissional_id=self.treinador.pk)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)

        Sessao = executor.loader.project_state(self.migrate_to).apps.get_model('app', 'Sessao')
        self.assertEqual(Sessao.objects.get(pk=sessao.pk).servico_id, self.servico.pk)

    def test_interrompe_e_preserva_sessao_sem_servico(self):
        sessao = self.criar_sessao(profissional_id=self.treinador.pk)

        executor = MigrationExecutor(connection)
        with self.assertRaisesMessage(RuntimeError, '1 sessão(ões) sem serviço e 0 sem profissional'):
            executor.migrate(self.migrate_to)

        Sessao = self.apps_anteriores.get_model('app', 'Sessao')
        self.assertTrue(Sessao.objects.filter(pk=sessao.pk, servico__isnull=True).exists())
