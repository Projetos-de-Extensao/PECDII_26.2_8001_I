from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from app.models import NotificacaoEmail, RelatorioTreino, Servico, Sessao, Usuario
from app.tests.helpers import criar_perfil

COMANDO = 'notificar_relatorios_pendentes'


def executar_comando():
    """Executa o comando sem poluir a saída dos testes."""
    call_command(COMANDO, stdout=StringIO(), stderr=StringIO())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LembreteRelatorioTests(TestCase):
    """Lembrete ao Treinador quando o relatório de treino segue pendente (RF-12)."""

    def setUp(self):
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-lembrete')
        self.outro_treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'outro-treinador')
        self.treino = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.sessao = self.criar_sessao(horas_desde_o_fim=25)

    def criar_sessao(self, horas_desde_o_fim, servico=None, profissional=None, status=Sessao.Status.REALIZADA):
        fim = timezone.now() - timedelta(hours=horas_desde_o_fim)
        return Sessao.objects.create(
            titulo='Treino da manhã',
            inicio=fim - timedelta(hours=1),
            fim=fim,
            servico=servico or self.treino,
            profissional=profissional or self.treinador,
            status=status,
        )

    # Elegibilidade e horário

    def test_envia_lembrete_quando_nao_ha_relatorio(self):
        executar_comando()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Treino da manhã', mail.outbox[0].subject)

    def test_envia_lembrete_quando_relatorio_esta_em_rascunho(self):
        RelatorioTreino.objects.create(sessao=self.sessao)

        executar_comando()

        self.assertEqual(len(mail.outbox), 1)

    def test_nao_envia_antes_de_24_horas_do_fim(self):
        self.sessao.delete()
        self.criar_sessao(horas_desde_o_fim=23)

        executar_comando()

        self.assertEqual(len(mail.outbox), 0)

    def test_nao_envia_com_relatorio_finalizado(self):
        RelatorioTreino.objects.create(
            sessao=self.sessao,
            status=RelatorioTreino.Status.FINALIZADO,
            finalizado_em=timezone.now(),
        )

        executar_comando()

        self.assertEqual(len(mail.outbox), 0)

    def test_nao_envia_para_atendimento_de_saude(self):
        self.sessao.delete()
        fisio = Servico.objects.create(nome='Fisioterapia', categoria=Servico.Categoria.FISIOTERAPIA)
        saude = criar_perfil(Usuario.Perfil.PROFISSIONAL_SAUDE, 'fisio-lembrete')
        self.criar_sessao(horas_desde_o_fim=25, servico=fisio, profissional=saude)

        executar_comando()

        self.assertEqual(len(mail.outbox), 0)

    def test_nao_envia_para_sessao_cancelada_ou_nao_realizada(self):
        self.sessao.delete()
        self.criar_sessao(horas_desde_o_fim=25, status=Sessao.Status.CANCELADA)
        self.criar_sessao(horas_desde_o_fim=26, status=Sessao.Status.NAO_REALIZADA)

        executar_comando()

        self.assertEqual(len(mail.outbox), 0)

    # Destinatário

    def test_envia_somente_ao_treinador_responsavel(self):
        executar_comando()

        self.assertEqual(mail.outbox[0].to, ['treinador-lembrete@example.com'])

    def test_ignora_treinador_sem_email(self):
        Usuario.objects.filter(pk=self.treinador.pk).update(email='')

        executar_comando()

        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(NotificacaoEmail.objects.exists())

    # Não duplicidade

    def test_registra_o_envio(self):
        executar_comando()

        notificacao = NotificacaoEmail.objects.get()
        self.assertEqual(notificacao.sessao, self.sessao)
        self.assertEqual(notificacao.tipo, NotificacaoEmail.Tipo.RELATORIO_PENDENTE)

    def test_execucoes_repetidas_enviam_um_unico_lembrete(self):
        executar_comando()
        executar_comando()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(NotificacaoEmail.objects.count(), 1)

    def test_execucao_concorrente_nao_envia_de_novo(self):
        """Simula outra execução que gravou o aviso entre a consulta e o envio."""
        criar_original = NotificacaoEmail.objects.create

        def outra_execucao_gravou_antes(**dados):
            criar_original(**dados)
            return criar_original(**dados)  # a restrição única do banco recusa a segunda gravação

        with mock.patch.object(NotificacaoEmail.objects, 'create', side_effect=outra_execucao_gravou_antes):
            executar_comando()

        self.assertEqual(len(mail.outbox), 0)

    def test_falha_no_envio_desfaz_registro_para_tentar_de_novo(self):
        with mock.patch(
            'app.management.commands.notificar_relatorios_pendentes.send_mail',
            side_effect=OSError('servidor indisponível'),
        ):
            executar_comando()
        self.assertFalse(NotificacaoEmail.objects.exists())

        executar_comando()

        self.assertEqual(len(mail.outbox), 1)
