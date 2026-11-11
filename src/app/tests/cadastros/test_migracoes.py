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
