from datetime import date, datetime, timedelta
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from app.models import Servico, Sessao, Usuario
from app.tests.helpers import cliente_autenticado, cliente_para, criar_perfil

SAO_PAULO = ZoneInfo('America/Sao_Paulo')
URL = '/api/dashboard/'


def momento(ano, mes, dia, hora=9, minuto=0):
    return datetime(ano, mes, dia, hora, minuto, tzinfo=SAO_PAULO)


class DashboardTests(TestCase):
    """GET /api/dashboard/ conta compromissos por serviço e situação no período (RF-11)."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-dashboard')
        self.client = cliente_para(self.admin)
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-dashboard')
        self.treino = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.fisio = Servico.objects.create(nome='Fisioterapia', categoria=Servico.Categoria.FISIOTERAPIA)
        self.nutricao = Servico.objects.create(nome='Nutrição', categoria=Servico.Categoria.NUTRICAO)

    def criar_sessao(self, servico, inicio, status=Sessao.Status.AGENDADA):
        return Sessao.objects.create(
            titulo='Compromisso',
            servico=servico,
            profissional=self.treinador,
            inicio=inicio,
            fim=inicio + timedelta(hours=1),
            status=status,
        )

    def consultar(self, **parametros):
        resposta = self.client.get(URL, parametros)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        return resposta.data

    @staticmethod
    def linha(dados, servico):
        return next(linha for linha in dados['servicos'] if linha['id'] == servico.pk)

    def test_conta_por_servico_e_situacao(self):
        self.criar_sessao(self.treino, momento(2026, 11, 3))
        self.criar_sessao(self.treino, momento(2026, 11, 4), Sessao.Status.REALIZADA)
        self.criar_sessao(self.treino, momento(2026, 11, 5), Sessao.Status.REALIZADA)
        self.criar_sessao(self.fisio, momento(2026, 11, 6), Sessao.Status.CANCELADA)

        dados = self.consultar(inicio='2026-11-01', fim='2026-11-30')

        self.assertEqual(
            self.linha(dados, self.treino)['por_situacao'],
            {'AGENDADA': 1, 'REALIZADA': 2, 'NAO_REALIZADA': 0, 'CANCELADA': 0},
        )
        self.assertEqual(self.linha(dados, self.treino)['total'], 3)
        self.assertEqual(self.linha(dados, self.fisio)['por_situacao']['CANCELADA'], 1)
        self.assertEqual(
            dados['total'],
            {
                'por_situacao': {'AGENDADA': 1, 'REALIZADA': 2, 'NAO_REALIZADA': 0, 'CANCELADA': 1},
                'total': 4,
            },
        )
        self.assertEqual(dados['periodo'], {'inicio': '2026-11-01', 'fim': '2026-11-30'})
        self.assertEqual(
            [situacao['valor'] for situacao in dados['situacoes']],
            ['AGENDADA', 'REALIZADA', 'NAO_REALIZADA', 'CANCELADA'],
        )

    def test_ordena_pelo_total_decrescente_e_depois_pelo_nome(self):
        self.criar_sessao(self.fisio, momento(2026, 11, 3))
        self.criar_sessao(self.fisio, momento(2026, 11, 4))
        self.criar_sessao(self.treino, momento(2026, 11, 5))

        dados = self.consultar(inicio='2026-11-01', fim='2026-11-30')

        self.assertEqual(
            [linha['nome'] for linha in dados['servicos']],
            ['Fisioterapia', 'Treino funcional', 'Nutrição'],
        )

    def test_servico_sem_compromissos_aparece_com_zeros(self):
        dados = self.consultar(inicio='2026-11-01', fim='2026-11-30')

        nutricao = self.linha(dados, self.nutricao)
        self.assertEqual(nutricao['total'], 0)
        self.assertEqual(set(nutricao['por_situacao'].values()), {0})
        self.assertEqual(dados['total']['total'], 0)

    def test_periodo_inclui_os_dois_dias_e_usa_o_fuso_do_projeto(self):
        # 30/11 às 23h30 em São Paulo já é 01/12 em UTC, mas pertence a novembro.
        self.criar_sessao(self.treino, momento(2026, 11, 1, 0, 0))
        self.criar_sessao(self.treino, momento(2026, 11, 30, 23, 30))
        self.criar_sessao(self.treino, momento(2026, 10, 31, 23, 30))
        self.criar_sessao(self.treino, momento(2026, 12, 1, 0, 0))

        dados = self.consultar(inicio='2026-11-01', fim='2026-11-30')

        self.assertEqual(self.linha(dados, self.treino)['total'], 2)

    def test_sem_periodo_usa_o_mes_atual(self):
        self.criar_sessao(self.treino, momento(2026, 11, 20))
        self.criar_sessao(self.treino, momento(2026, 10, 20))

        with mock.patch('app.operacao.timezone.localdate', return_value=date(2026, 11, 11)):
            dados = self.consultar()

        self.assertEqual(dados['periodo'], {'inicio': '2026-11-01', 'fim': '2026-11-30'})
        self.assertEqual(self.linha(dados, self.treino)['total'], 1)

    def test_mes_atual_em_dezembro_termina_no_dia_31(self):
        with mock.patch('app.operacao.timezone.localdate', return_value=date(2026, 12, 15)):
            dados = self.consultar()

        self.assertEqual(dados['periodo'], {'inicio': '2026-12-01', 'fim': '2026-12-31'})

    def test_periodo_invalido_responde_400(self):
        casos = [
            {'inicio': '2026-11-01'},
            {'fim': '2026-11-30'},
            {'inicio': '2026-11-30', 'fim': '2026-11-01'},
            {'inicio': '01/11/2026', 'fim': '2026-11-30'},
        ]
        for parametros in casos:
            with self.subTest(parametros=parametros):
                self.assertEqual(self.client.get(URL, parametros).status_code, 400)

    def test_periodo_de_um_dia_e_aceito(self):
        self.criar_sessao(self.treino, momento(2026, 11, 3))

        dados = self.consultar(inicio='2026-11-03', fim='2026-11-03')

        self.assertEqual(self.linha(dados, self.treino)['total'], 1)


class DashboardAcessoTests(TestCase):
    """O dashboard é exclusivo do Administrador (RF-11)."""

    def test_sem_autenticacao_responde_401(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)

    def test_perfis_profissionais_recebem_403(self):
        for perfil in Usuario.PERFIS_PROFISSIONAIS:
            with self.subTest(perfil=perfil):
                cliente = cliente_autenticado(perfil, f'dashboard-{perfil.lower()}')
                self.assertEqual(cliente.get(URL).status_code, 403)

    def test_superusuario_consulta_como_administrador(self):
        conta = get_user_model().objects.create_superuser(username='raiz-dashboard')
        self.assertEqual(cliente_para(conta).get(URL).status_code, 200)

    def test_dashboard_e_somente_leitura(self):
        cliente = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-dashboard-escrita')
        self.assertEqual(cliente.post(URL, {}).status_code, 405)
