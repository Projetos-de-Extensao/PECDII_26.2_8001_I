from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import Aluno, Participacao, Servico, Sessao, Usuario
from app.tests.helpers import cliente_autenticado, cliente_para, criar_perfil

URL = '/api/pendencias/'
PRESENTE = Participacao.SituacaoPresenca.PRESENTE
FALTA = Participacao.SituacaoPresenca.FALTA


class PendenciasTests(TestCase):
    """GET /api/pendencias/ lista compromissos encerrados com presença pendente (RF-09, D-11)."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-pendencias')
        self.client = cliente_para(self.admin)
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-pendencias', nome='Carla Dias')
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.ana = Aluno.objects.create(nome='Ana Lima', data_nascimento='2010-03-01')
        self.bruno = Aluno.objects.create(nome='Bruno Costa', data_nascimento='2011-07-15')
        self.agora = timezone.now()

    def criar_sessao(self, fim, presencas, status=Sessao.Status.AGENDADA):
        """Cria a sessão terminando em `fim`, com um participante por item de `presencas`."""
        sessao = Sessao.objects.create(
            titulo='Treino de força',
            servico=self.servico,
            profissional=self.treinador,
            inicio=fim - timedelta(hours=1),
            fim=fim,
            status=status,
        )
        for aluno, situacao in zip([self.ana, self.bruno], presencas):
            Participacao.objects.create(sessao=sessao, aluno=aluno, situacao_presenca=situacao)
        return sessao

    def consultar(self, **parametros):
        resposta = self.client.get(URL, parametros)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        return resposta.data

    def ids(self, dados):
        return [item['sessao']['id'] for item in dados['itens']]

    def test_lista_sessao_encerrada_com_participante_sem_registro(self):
        sessao = self.criar_sessao(self.agora - timedelta(hours=2), [PRESENTE, None])

        dados = self.consultar()

        self.assertEqual(dados['total'], 1)
        self.assertEqual(dados['por_tipo'], {'PRESENCA_PENDENTE': 1})
        item = dados['itens'][0]
        self.assertEqual(item['tipo'], 'PRESENCA_PENDENTE')
        self.assertEqual(item['motivo'], '1 de 2 participante(s) sem presença ou falta registrada.')
        self.assertEqual(item['responsavel'], {'id': self.treinador.pk, 'nome': 'Carla Dias'})
        self.assertEqual(item['sessao']['id'], sessao.pk)
        self.assertEqual(item['sessao']['servico']['nome'], 'Treino funcional')
        self.assertEqual(item['sessao']['status'], 'AGENDADA')
        self.assertEqual(item['detalhe'], f'/api/sessoes/{sessao.pk}/')

    def test_ignora_o_que_nao_e_pendencia(self):
        self.criar_sessao(self.agora - timedelta(hours=2), [PRESENTE, FALTA])
        self.criar_sessao(self.agora - timedelta(hours=2), [None], Sessao.Status.CANCELADA)
        self.criar_sessao(self.agora + timedelta(minutes=30), [None])
        self.criar_sessao(self.agora - timedelta(hours=2), [])

        dados = self.consultar()

        self.assertEqual(dados['total'], 0)
        self.assertEqual(dados['itens'], [])
        self.assertEqual(dados['por_tipo'], {'PRESENCA_PENDENTE': 0})

    def test_sessao_nao_realizada_com_presenca_pendente_continua_pendente(self):
        # D-11 só exclui as canceladas; a situação da sessão é independente da presença (RF-10).
        sessao = self.criar_sessao(self.agora - timedelta(hours=2), [None], Sessao.Status.NAO_REALIZADA)

        self.assertEqual(self.ids(self.consultar()), [sessao.pk])

    def test_sessao_que_termina_agora_ja_e_pendente(self):
        sessao = self.criar_sessao(self.agora - timedelta(seconds=1), [None])

        self.assertEqual(self.ids(self.consultar()), [sessao.pk])

    def test_ordena_da_mais_antiga_para_a_mais_recente(self):
        recente = self.criar_sessao(self.agora - timedelta(hours=1), [None])
        antiga = self.criar_sessao(self.agora - timedelta(days=3), [None])

        self.assertEqual(self.ids(self.consultar()), [antiga.pk, recente.pk])

    def test_filtra_por_tipo(self):
        sessao = self.criar_sessao(self.agora - timedelta(hours=2), [None])

        dados = self.consultar(tipo='PRESENCA_PENDENTE')

        self.assertEqual(self.ids(dados), [sessao.pk])
        self.assertEqual([tipo['valor'] for tipo in dados['tipos']], ['PRESENCA_PENDENTE'])

    def test_tipo_desconhecido_responde_400(self):
        self.assertEqual(self.client.get(URL, {'tipo': 'RELATORIO_INEXISTENTE'}).status_code, 400)

    def test_atalho_abre_a_sessao_mas_nao_permite_ao_administrador_registrar_presenca(self):
        self.criar_sessao(self.agora - timedelta(hours=2), [None])
        detalhe = self.consultar()['itens'][0]['detalhe']

        self.assertEqual(self.client.get(detalhe).status_code, 200)
        resposta = self.client.patch(
            f'{detalhe}presencas/',
            {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]},
            format='json',
        )
        self.assertEqual(resposta.status_code, 403)

    def test_presenca_registrada_tira_a_sessao_da_lista(self):
        sessao = self.criar_sessao(self.agora - timedelta(hours=2), [None])
        responsavel = cliente_para(self.treinador)

        resposta = responsavel.patch(
            f'/api/sessoes/{sessao.pk}/presencas/',
            {'presencas': [{'aluno': self.ana.pk, 'situacao': 'FALTA'}]},
            format='json',
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.consultar()['total'], 0)


class PendenciasAcessoTests(TestCase):
    """A consulta de pendências é exclusiva do Administrador (RF-09)."""

    def test_sem_autenticacao_responde_401(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)

    def test_perfis_profissionais_recebem_403(self):
        for perfil in Usuario.PERFIS_PROFISSIONAIS:
            with self.subTest(perfil=perfil):
                cliente = cliente_autenticado(perfil, f'pendencias-{perfil.lower()}')
                self.assertEqual(cliente.get(URL).status_code, 403)

    def test_superusuario_consulta_como_administrador(self):
        conta = get_user_model().objects.create_superuser(username='raiz-pendencias')
        self.assertEqual(cliente_para(conta).get(URL).status_code, 200)

    def test_consulta_e_somente_leitura(self):
        cliente = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-pendencias-escrita')
        self.assertEqual(cliente.post(URL, {}).status_code, 405)
