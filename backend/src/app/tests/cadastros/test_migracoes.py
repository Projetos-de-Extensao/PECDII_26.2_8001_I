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
            pk=1,
            nome='Bruno Costa',
            email='bruno-legado@example.com',
            telefone='+5521912345678',
        )
        ProfessorAntigo.objects.create(
            pk=2,
            nome='Ana Lima',
            email='ana-legada@example.com',
            telefone='+5521912345679',
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

    def preparar_sessao_para_migracao_0015(self):
        alvo_pre_0015 = [('app', '0014_participacao_servico_da_sessao')]
        executor = MigrationExecutor(connection)
        executor.migrate(alvo_pre_0015)
        apps_pre_0015 = executor.loader.project_state(alvo_pre_0015).apps
        Servico = apps_pre_0015.get_model('app', 'Servico')
        Sessao = apps_pre_0015.get_model('app', 'Sessao')
        servico = Servico.objects.create(nome='Treino legado', categoria='TREINO')
        Sessao.objects.filter(pk=self.sessao_id).update(servico_id=servico.pk)

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

    def test_simplifica_logins_legados_e_permite_reverter(self):
        self.preparar_sessao_para_migracao_0015()
        alvo_final = [('app', '0017_simplificar_login_professor_migrado')]
        executor = MigrationExecutor(connection)
        executor.migrate(alvo_final)
        apps_finais = executor.loader.project_state(alvo_final).apps
        UsuarioFinal = apps_finais.get_model('app', 'Usuario')

        perfil_um = UsuarioFinal.objects.get(email='bruno-legado@example.com')
        perfil_dois = UsuarioFinal.objects.get(email='ana-legada@example.com')
        sessao = apps_finais.get_model('app', 'Sessao').objects.get(pk=self.sessao_id)

        self.assertEqual(perfil_um.conta.username, 'usuario')
        self.assertEqual(perfil_dois.conta.username, 'usuario-2')
        self.assertTrue(perfil_um.conta.password.startswith('!'))
        self.assertEqual(sessao.profissional_id, perfil_um.pk)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        apps_revertidas = executor.loader.project_state(self.migrate_to).apps
        UsuarioRevertido = apps_revertidas.get_model('app', 'Usuario')
        self.assertEqual(
            UsuarioRevertido.objects.get(email='bruno-legado@example.com').conta.username,
            f'gaap-migrado-professor-{self.professor_id}',
        )

    def test_nao_sobrescreve_um_login_professor_ja_existente(self):
        self.preparar_sessao_para_migracao_0015()
        ContaHistorica = self.apps_migradas.get_model('auth', 'User')
        conta_conflitante = ContaHistorica.objects.create(username='usuario', password='!')

        executor = MigrationExecutor(connection)
        with self.assertRaisesRegex(RuntimeError, 'já pertence a outra conta'):
            executor.migrate([('app', '0017_simplificar_login_professor_migrado')])

        ContaAindaMigrada = self.apps_migradas.get_model('auth', 'User')
        self.assertTrue(
            ContaAindaMigrada.objects.filter(
                username=f'gaap-migrado-professor-{self.professor_id}',
            ).exists()
        )
        conta_conflitante.delete()

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
