from datetime import timedelta

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
        self.assertEqual(response.data['telefone'], '+55 (11) 98765-4321')

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
        self.assertEqual(response.data['telefone'], '+55 (21) 91234-5678')

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
    """Verifica criação, pendências e confirmação de sessões."""

    def setUp(self):
        self.client = APIClient()
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
            confirmacao_realizacao=Sessao.Confirmacao.OCORREU,
        )

        response = self.client.get('/api/sessoes/pendentes-confirmacao/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [vencida.pk])
        self.assertNotIn(recente.pk, [item['id'] for item in response.data])

    def test_confirma_sessao_realizada_e_salva_observacoes(self):
        sessao = self.criar_sessao()

        response = self.client.post(
            f'/api/sessoes/{sessao.pk}/confirmar-realizacao/',
            {'ocorreu': True, 'observacoes': 'Treino de força concluído.'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.REALIZADA)
        self.assertEqual(sessao.confirmacao_realizacao, Sessao.Confirmacao.OCORREU)
        self.assertEqual(sessao.observacoes, 'Treino de força concluído.')

    def test_confirma_sessao_nao_realizada(self):
        sessao = self.criar_sessao()

        response = self.client.post(
            f'/api/sessoes/{sessao.pk}/confirmar-realizacao/',
            {'ocorreu': False},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.NAO_REALIZADA)
        self.assertEqual(sessao.confirmacao_realizacao, Sessao.Confirmacao.NAO_OCORREU)

    def test_nao_permite_confirmar_antes_dos_30_minutos(self):
        fim = timezone.now() - timedelta(minutes=29)
        sessao = self.criar_sessao(
            inicio=fim - timedelta(hours=1),
            fim=fim,
        )

        response = self.client.post(
            f'/api/sessoes/{sessao.pk}/confirmar-realizacao/',
            {'ocorreu': True},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.AGENDADA)

    def test_rejeita_valor_nao_booleano_para_ocorreu(self):
        sessao = self.criar_sessao()

        response = self.client.post(
            f'/api/sessoes/{sessao.pk}/confirmar-realizacao/',
            {'ocorreu': 'sim'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificacaoSessaoTests(TestCase):
    """Verifica o comando que avisa sobre sessões sem confirmação."""

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
