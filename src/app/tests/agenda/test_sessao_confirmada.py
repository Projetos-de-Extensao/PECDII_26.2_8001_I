from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from app.models import BloqueioAgenda, Disponibilidade, Servico, Sessao, Usuario
from app.tests.helpers import cliente_para, criar_perfil


class AgendaComSessaoConfirmadaTests(TestCase):
    """Disponibilidade e bloqueio não deixam sessão confirmada fora da agenda (RN-03, D-18, #119)."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-agenda-confirmada')
        self.client = cliente_para(self.admin)
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-agenda-confirmada')
        self.outro = criar_perfil(Usuario.Perfil.TREINADOR, 'outro-agenda-confirmada')
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)

        self.base = (timezone.now() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
        self.disponibilidade = Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=self.base - timedelta(hours=3),
            fim=self.base + timedelta(hours=3),
        )
        self.sessao = self.criar_sessao(self.base, self.base + timedelta(hours=1))

    def criar_sessao(self, inicio, fim, status=Sessao.Status.AGENDADA, profissional=None):
        return Sessao.objects.create(
            titulo='Treino de força',
            servico=self.servico,
            profissional=profissional or self.treinador,
            inicio=inicio,
            fim=fim,
            status=status,
        )

    def url_disponibilidade(self, disponibilidade=None):
        return f'/api/disponibilidades/{(disponibilidade or self.disponibilidade).pk}/'

    def assert_conflito(self, resposta, sessao=None):
        sessao = sessao or self.sessao
        self.assertEqual(resposta.status_code, 409, resposta.data)
        self.assertEqual(resposta.data['regra'], 'RN-03')
        self.assertEqual(resposta.data['sessao'], sessao.pk)
        self.assertIn(f'sessão {sessao.pk}', resposta.data['detail'])

    # Disponibilidade

    def test_remover_disponibilidade_que_cobre_sessao_responde_409(self):
        resposta = self.client.delete(self.url_disponibilidade())

        self.assert_conflito(resposta)
        self.assertIn('fora da disponibilidade', resposta.data['detail'])
        self.assertTrue(Disponibilidade.objects.filter(pk=self.disponibilidade.pk).exists())

    def test_remover_disponibilidade_e_permitido_se_outra_cobre_a_sessao(self):
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=self.base - timedelta(hours=1),
            fim=self.base + timedelta(hours=2),
        )

        self.assertEqual(self.client.delete(self.url_disponibilidade()).status_code, 204)

    def test_duas_disponibilidades_que_so_juntas_cobrem_a_sessao_nao_bastam(self):
        # A confirmação exige uma disponibilidade que abranja a sessão inteira (RN-03).
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=self.base - timedelta(hours=1),
            fim=self.base + timedelta(minutes=30),
        )
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=self.base + timedelta(minutes=30),
            fim=self.base + timedelta(hours=2),
        )

        self.assert_conflito(self.client.delete(self.url_disponibilidade()))

    def test_sessao_cancelada_nao_impede_remover_disponibilidade(self):
        self.sessao.status = Sessao.Status.CANCELADA
        self.sessao.save()

        self.assertEqual(self.client.delete(self.url_disponibilidade()).status_code, 204)

    def test_sessao_ja_encerrada_nao_impede_remover_disponibilidade(self):
        ontem = timezone.now() - timedelta(days=1)
        antiga = Disponibilidade.objects.create(
            profissional=self.treinador, inicio=ontem - timedelta(hours=2), fim=ontem + timedelta(hours=2)
        )
        self.criar_sessao(ontem, ontem + timedelta(hours=1), Sessao.Status.REALIZADA)

        self.assertEqual(self.client.delete(self.url_disponibilidade(antiga)).status_code, 204)

    def test_remover_disponibilidade_sem_sessao_dentro_e_permitido(self):
        livre = Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=self.base + timedelta(days=5),
            fim=self.base + timedelta(days=5, hours=4),
        )

        self.assertEqual(self.client.delete(self.url_disponibilidade(livre)).status_code, 204)

    def test_reduzir_disponibilidade_que_deixa_sessao_de_fora_responde_409(self):
        resposta = self.client.patch(
            self.url_disponibilidade(),
            {'fim': (self.base + timedelta(minutes=30)).isoformat()},
            format='json',
        )

        self.assert_conflito(resposta)
        self.disponibilidade.refresh_from_db()
        self.assertEqual(self.disponibilidade.fim, self.base + timedelta(hours=3))

    def test_alterar_disponibilidade_que_continua_cobrindo_a_sessao_e_permitido(self):
        resposta = self.client.patch(
            self.url_disponibilidade(),
            {'inicio': (self.base - timedelta(hours=1)).isoformat()},
            format='json',
        )

        self.assertEqual(resposta.status_code, 200, resposta.data)

    def test_trocar_o_profissional_da_disponibilidade_responde_409(self):
        resposta = self.client.put(
            self.url_disponibilidade(),
            {
                'profissional': self.outro.pk,
                'inicio': self.disponibilidade.inicio.isoformat(),
                'fim': self.disponibilidade.fim.isoformat(),
            },
            format='json',
        )

        self.assert_conflito(resposta)

    # Bloqueio

    def bloquear(self, inicio, fim, profissional=None):
        return self.client.post(
            '/api/bloqueios-agenda/',
            {
                'profissional': (profissional or self.treinador).pk,
                'inicio': inicio.isoformat(),
                'fim': fim.isoformat(),
                'motivo': 'Reunião',
            },
            format='json',
        )

    def test_bloqueio_sobre_sessao_confirmada_responde_409(self):
        resposta = self.bloquear(self.base + timedelta(minutes=30), self.base + timedelta(hours=2))

        self.assert_conflito(resposta)
        self.assertIn('bloqueio se sobrepõe', resposta.data['detail'])
        self.assertFalse(BloqueioAgenda.objects.exists())

    def test_bloqueio_contiguo_a_sessao_e_permitido(self):
        resposta = self.bloquear(self.base - timedelta(hours=1), self.base)

        self.assertEqual(resposta.status_code, 201, resposta.data)

    def test_bloqueio_sobre_sessao_cancelada_e_permitido(self):
        self.sessao.status = Sessao.Status.CANCELADA
        self.sessao.save()

        resposta = self.bloquear(self.base, self.base + timedelta(hours=1))

        self.assertEqual(resposta.status_code, 201, resposta.data)

    def test_bloqueio_de_outro_profissional_no_mesmo_horario_e_permitido(self):
        resposta = self.bloquear(self.base, self.base + timedelta(hours=1), profissional=self.outro)

        self.assertEqual(resposta.status_code, 201, resposta.data)

    def test_bloqueio_sobre_sessao_em_andamento_responde_409(self):
        agora = timezone.now()
        em_andamento = self.criar_sessao(agora - timedelta(minutes=30), agora + timedelta(minutes=30))

        resposta = self.bloquear(agora, agora + timedelta(hours=1))

        self.assert_conflito(resposta, em_andamento)

    def test_mover_bloqueio_para_cima_da_sessao_responde_409(self):
        bloqueio = BloqueioAgenda.objects.create(
            profissional=self.treinador,
            inicio=self.base - timedelta(hours=2),
            fim=self.base - timedelta(hours=1),
        )

        resposta = self.client.patch(
            f'/api/bloqueios-agenda/{bloqueio.pk}/',
            {'fim': (self.base + timedelta(minutes=15)).isoformat()},
            format='json',
        )

        self.assert_conflito(resposta)
        bloqueio.refresh_from_db()
        self.assertEqual(bloqueio.fim, self.base - timedelta(hours=1))

    def test_editar_motivo_de_bloqueio_sem_conflito_e_permitido(self):
        bloqueio = BloqueioAgenda.objects.create(
            profissional=self.treinador,
            inicio=self.base - timedelta(hours=2),
            fim=self.base - timedelta(hours=1),
        )

        resposta = self.client.patch(
            f'/api/bloqueios-agenda/{bloqueio.pk}/', {'motivo': 'Consulta médica'}, format='json'
        )

        self.assertEqual(resposta.status_code, 200, resposta.data)
