from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import Servico, Sessao, Usuario
from app.tests.helpers import criar_usuario


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificacaoSessaoTests(TestCase):
    """Verifica avisos para sessões que continuam agendadas após o horário."""

    def setUp(self):
        self.profissional_conta = criar_usuario(Usuario.Perfil.TREINADOR, 'responsavel-notificacao')
        self.profissional = self.profissional_conta.usuario
        servico = Servico.objects.create(nome='Avaliação física', categoria=Servico.Categoria.TREINO)
        agora = timezone.now()
        self.sessao = Sessao.objects.create(
            titulo='Avaliação inicial',
            tipo=Sessao.Tipo.AVALIACAO,
            inicio=agora - timedelta(hours=2),
            fim=agora - timedelta(minutes=31),
            servico=servico,
            profissional=self.profissional,
        )

    def test_envia_email_e_marca_notificacao(self):
        call_command('notificar_sessoes_pendentes')

        self.sessao.refresh_from_db()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['responsavel-notificacao@example.com'])
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
