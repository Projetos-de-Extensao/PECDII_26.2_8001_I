from datetime import datetime, timedelta, timezone as timezone_utc

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from app.models import BloqueioAgenda, Disponibilidade, Usuario


class ConfiguracaoAgendaApiTests(TestCase):
    """Verifica CRUD, validação e autorização da configuração da agenda."""

    def setUp(self):
        self.admin = self.criar_usuario('admin-agenda', Usuario.Perfil.ADMINISTRADOR)
        self.treinador = self.criar_usuario('treinador-agenda', Usuario.Perfil.TREINADOR)
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin.conta)
        self.treinador_client = APIClient()
        self.treinador_client.force_authenticate(self.treinador.conta)
        self.inicio = datetime(2026, 11, 10, 9, tzinfo=timezone_utc.utc)
        self.fim = self.inicio + timedelta(hours=1)

    def criar_usuario(self, login, perfil):
        conta = get_user_model().objects.create_user(username=login)
        return Usuario.objects.create(
            conta=conta,
            nome=login,
            email=f'{login}@example.com',
            perfil=perfil,
        )

    def dados_faixa(self, **extras):
        dados = {
            'profissional': self.treinador.pk,
            'inicio': self.inicio.isoformat(),
            'fim': self.fim.isoformat(),
        }
        dados.update(extras)
        return dados

    def test_administrador_executa_crud_de_disponibilidade(self):
        criado = self.admin_client.post('/api/disponibilidades/', self.dados_faixa(), format='json')
        self.assertEqual(criado.status_code, 201)

        atualizado = self.admin_client.patch(
            f"/api/disponibilidades/{criado.data['id']}/",
            {'fim': (self.fim + timedelta(hours=1)).isoformat()},
            format='json',
        )
        removido = self.admin_client.delete(f"/api/disponibilidades/{criado.data['id']}/")

        self.assertEqual(atualizado.status_code, 200)
        self.assertEqual(removido.status_code, 204)
        self.assertFalse(Disponibilidade.objects.exists())

    def test_administrador_executa_crud_de_bloqueio(self):
        criado = self.admin_client.post(
            '/api/bloqueios-agenda/', self.dados_faixa(motivo='Feriado'), format='json'
        )
        self.assertEqual(criado.status_code, 201)
        self.assertEqual(criado.data['motivo'], 'Feriado')

        atualizado = self.admin_client.patch(
            f"/api/bloqueios-agenda/{criado.data['id']}/",
            {'motivo': 'Recesso'},
            format='json',
        )
        removido = self.admin_client.delete(f"/api/bloqueios-agenda/{criado.data['id']}/")

        self.assertEqual(atualizado.status_code, 200)
        self.assertEqual(atualizado.data['motivo'], 'Recesso')
        self.assertEqual(removido.status_code, 204)
        self.assertFalse(BloqueioAgenda.objects.exists())

    def test_treinador_pode_consultar_mas_nao_alterar_configuracao(self):
        faixa = Disponibilidade.objects.create(
            profissional=self.treinador, inicio=self.inicio, fim=self.fim
        )

        consulta = self.treinador_client.get('/api/disponibilidades/')
        criacao = self.treinador_client.post(
            '/api/disponibilidades/', self.dados_faixa(), format='json'
        )
        alteracao = self.treinador_client.patch(
            f'/api/disponibilidades/{faixa.pk}/',
            {'fim': (self.fim + timedelta(hours=1)).isoformat()},
            format='json',
        )
        exclusao = self.treinador_client.delete(f'/api/disponibilidades/{faixa.pk}/')

        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(criacao.status_code, 403)
        self.assertEqual(alteracao.status_code, 403)
        self.assertEqual(exclusao.status_code, 403)
        self.assertEqual(Disponibilidade.objects.count(), 1)

    def test_intervalo_invalido_e_recusado_sem_persistir(self):
        dados = self.dados_faixa(inicio=self.fim.isoformat(), fim=self.inicio.isoformat())

        disponibilidade = self.admin_client.post('/api/disponibilidades/', dados, format='json')
        bloqueio = self.admin_client.post('/api/bloqueios-agenda/', dados, format='json')

        self.assertEqual(disponibilidade.status_code, 400)
        self.assertEqual(bloqueio.status_code, 400)
        self.assertIn('fim', disponibilidade.data)
        self.assertIn('fim', bloqueio.data)
        self.assertFalse(Disponibilidade.objects.exists())
        self.assertFalse(BloqueioAgenda.objects.exists())

    def test_bloqueio_valida_motivo_e_perfil_do_profissional(self):
        motivo_longo = self.admin_client.post(
            '/api/bloqueios-agenda/', self.dados_faixa(motivo='x' * 201), format='json'
        )
        administrador_como_profissional = self.admin_client.post(
            '/api/bloqueios-agenda/',
            self.dados_faixa(profissional=self.admin.pk, motivo='Manutenção'),
            format='json',
        )

        self.assertEqual(motivo_longo.status_code, 400)
        self.assertEqual(administrador_como_profissional.status_code, 400)
        self.assertFalse(BloqueioAgenda.objects.exists())

    def test_consulta_sem_autenticacao_e_recusada(self):
        cliente = APIClient()

        self.assertEqual(cliente.get('/api/disponibilidades/').status_code, 401)
        self.assertEqual(cliente.get('/api/bloqueios-agenda/').status_code, 401)


class ConfiguracaoAgendaModelTests(TestCase):
    """Verifica as restrições dos modelos de disponibilidade e bloqueio."""

    def setUp(self):
        conta = get_user_model().objects.create_user(username='modelo-agenda')
        self.treinador = Usuario.objects.create(
            conta=conta,
            nome='Treinador',
            email='modelo-agenda@example.com',
            perfil=Usuario.Perfil.TREINADOR,
        )
        self.inicio = datetime(2026, 11, 10, 9, tzinfo=timezone_utc.utc)
        self.fim = self.inicio + timedelta(hours=1)

    def test_modelos_rejeitam_intervalo_invalido(self):
        disponibilidade = Disponibilidade(
            profissional=self.treinador, inicio=self.fim, fim=self.inicio
        )
        bloqueio = BloqueioAgenda(
            profissional=self.treinador, inicio=self.fim, fim=self.inicio
        )

        with self.assertRaises(ValidationError):
            disponibilidade.full_clean()
        with self.assertRaises(ValidationError):
            bloqueio.full_clean()

    def test_banco_impede_intervalos_invalidos_em_gravacao_em_lote(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Disponibilidade.objects.bulk_create([
                    Disponibilidade(
                        profissional=self.treinador, inicio=self.fim, fim=self.inicio
                    )
                ])
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BloqueioAgenda.objects.bulk_create([
                    BloqueioAgenda(
                        profissional=self.treinador, inicio=self.fim, fim=self.inicio
                    )
                ])

    def test_bloqueio_aceita_motivo_opcional_de_ate_duzentos_caracteres(self):
        bloqueio = BloqueioAgenda(
            profissional=self.treinador,
            inicio=self.inicio,
            fim=self.fim,
            motivo='x' * 200,
        )

        bloqueio.full_clean()
        bloqueio.save()
        self.assertEqual(bloqueio.motivo, 'x' * 200)

    def test_profissional_com_configuracao_nao_pode_virar_administrador(self):
        Disponibilidade.objects.create(
            profissional=self.treinador, inicio=self.inicio, fim=self.fim
        )
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR

        with self.assertRaises(ValidationError):
            self.treinador.save()

        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.TREINADOR)


class ConfiguracaoAgendaMigrationTests(TransactionTestCase):
    """Confere que a migração 0013 cria os modelos e as estruturas de agenda."""

    migrate_from = [('app', '0012_migrar_professor_para_usuario')]
    migrate_to = [('app', '0013_bloqueioagenda_disponibilidade')]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps_migradas = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migracao_cria_tabelas_indices_e_restricoes(self):
        disponibilidade = self.apps_migradas.get_model('app', 'Disponibilidade')
        bloqueio = self.apps_migradas.get_model('app', 'BloqueioAgenda')

        with connection.cursor() as cursor:
            tabelas = connection.introspection.table_names(cursor)
            constraints_disponibilidade = connection.introspection.get_constraints(
                cursor, disponibilidade._meta.db_table
            )
            constraints_bloqueio = connection.introspection.get_constraints(
                cursor, bloqueio._meta.db_table
            )

        self.assertIn(disponibilidade._meta.db_table, tabelas)
        self.assertIn(bloqueio._meta.db_table, tabelas)
        self.assertIn('disp_prof_inicio_idx', constraints_disponibilidade)
        self.assertIn('disponibilidade_fim_apos_inicio', constraints_disponibilidade)
        self.assertIn('bloq_prof_inicio_idx', constraints_bloqueio)
        self.assertIn('bloqueio_fim_apos_inicio', constraints_bloqueio)
