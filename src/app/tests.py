from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import Aluno, Professor, Sessao


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TelefoneApiTests(TestCase):
    """Verifica a validação e normalização de telefones pela API."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=get_user_model().objects.create_user(username='teste-api-aluno')
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

    def test_professor_telefone_com_ddi_e_mascara_e_normalizado(self):
        response = self.client.post(
            '/api/professores/',
            {
                'nome': 'Bruno Costa',
                'email': 'bruno@example.com',
                'telefone': '+55 21 91234-5678',
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


class SessaoApiTests(TestCase):
    """Verifica criação, pendências e atualização do status das sessões."""

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(
            user=get_user_model().objects.create_user(username='teste-api-sessao')
        )
        self.professor = Professor.objects.create(
            nome='Bruno Costa',
            email='bruno@example.com',
        )

    def criar_sessao(self, **overrides):
        agora = timezone.now()
        dados = {
            'titulo': 'Treino funcional',
            'tipo': Sessao.Tipo.TREINAMENTO,
            'inicio': agora - timedelta(hours=2),
            'fim': agora - timedelta(hours=1),
            'professor': self.professor,
        }
        dados.update(overrides)
        return Sessao.objects.create(**dados)

    def test_cria_sessao_com_professor_tipo_e_descricao(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.client.post(
            '/api/sessoes/',
            {
                'titulo': 'Avaliação inicial',
                'tipo': Sessao.Tipo.AVALIACAO,
                'descricao': 'Avaliação de mobilidade e força.',
                'inicio': inicio.isoformat(),
                'fim': (inicio + timedelta(minutes=60)).isoformat(),
                'professor': self.professor.pk,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tipo'], Sessao.Tipo.AVALIACAO)
        self.assertEqual(response.data['descricao'], 'Avaliação de mobilidade e força.')
        self.assertEqual(response.data['professor'], self.professor.pk)

    def test_criacao_sem_professor_e_rejeitada(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.client.post(
            '/api/sessoes/',
            {
                'titulo': 'Treino funcional',
                'tipo': Sessao.Tipo.TREINAMENTO,
                'inicio': inicio.isoformat(),
                'fim': (inicio + timedelta(minutes=60)).isoformat(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('professor', response.data)

    def test_fim_anterior_ao_inicio_e_rejeitado(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.client.post(
            '/api/sessoes/',
            {
                'titulo': 'Treino funcional',
                'tipo': Sessao.Tipo.TREINAMENTO,
                'inicio': inicio.isoformat(),
                'fim': (inicio - timedelta(minutes=1)).isoformat(),
                'professor': self.professor.pk,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('fim', response.data)

    def test_lista_somente_sessoes_pendentes_com_mais_de_30_minutos(self):
        vencida = self.criar_sessao()
        recente = self.criar_sessao(
            titulo='Sessão recente',
            inicio=timezone.now() - timedelta(minutes=50),
            fim=timezone.now() - timedelta(minutes=20),
        )
        self.criar_sessao(
            titulo='Já realizada',
            status=Sessao.Status.REALIZADA,
        )

        response = self.client.get('/api/sessoes/pendentes-status/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [vencida.pk])
        self.assertNotIn(recente.pk, [item['id'] for item in response.data])

    def test_atualiza_status_para_realizada_e_salva_observacoes(self):
        sessao = self.criar_sessao()

        response = self.client.patch(
            f'/api/sessoes/{sessao.pk}/',
            {'status': Sessao.Status.REALIZADA, 'observacoes': 'Treino de força concluído.'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.REALIZADA)
        self.assertEqual(sessao.observacoes, 'Treino de força concluído.')

    def test_atualiza_status_para_nao_realizada(self):
        sessao = self.criar_sessao()

        response = self.client.patch(
            f'/api/sessoes/{sessao.pk}/',
            {'status': Sessao.Status.NAO_REALIZADA},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.NAO_REALIZADA)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificacaoSessaoTests(TestCase):
    """Verifica avisos para sessões que continuam agendadas após o horário."""

    def setUp(self):
        self.professor = Professor.objects.create(
            nome='Bruno Costa',
            email='bruno@example.com',
        )
        agora = timezone.now()
        self.sessao = Sessao.objects.create(
            titulo='Avaliação inicial',
            tipo=Sessao.Tipo.AVALIACAO,
            inicio=agora - timedelta(hours=2),
            fim=agora - timedelta(minutes=31),
            professor=self.professor,
        )

    def test_envia_email_e_marca_notificacao(self):
        call_command('notificar_sessoes_pendentes')

        self.sessao.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['bruno@example.com'])
        self.assertIsNotNone(self.sessao.notificacao_enviada_em)

    def test_nao_envia_email_duplicado(self):
        call_command('notificar_sessoes_pendentes')
        call_command('notificar_sessoes_pendentes')

        self.assertEqual(len(mail.outbox), 1)

    def test_nao_notifica_sessao_cancelada(self):
        self.sessao.status = Sessao.Status.CANCELADA
        self.sessao.save(update_fields=['status'])

        call_command('notificar_sessoes_pendentes')

        self.assertEqual(len(mail.outbox), 0)

    def test_nao_notifica_sessao_com_status_atualizado(self):
        self.sessao.status = Sessao.Status.REALIZADA
        self.sessao.save(update_fields=['status'])

        call_command('notificar_sessoes_pendentes')

        self.assertEqual(len(mail.outbox), 0)
