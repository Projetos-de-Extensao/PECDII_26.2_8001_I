from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import Aluno, Participacao, RelatorioTreino, Servico, Sessao, Usuario
from app.tests.helpers import cliente_autenticado, cliente_para, criar_perfil

URL = '/api/pendencias/'
PRESENTE = Participacao.SituacaoPresenca.PRESENTE
FALTA = Participacao.SituacaoPresenca.FALTA


class BasePendenciasTests(TestCase):
    """Cria o Administrador, um Treinador, um serviço de Treino e dois alunos."""

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


class PendenciasTests(BasePendenciasTests):
    """GET /api/pendencias/ lista compromissos encerrados com presença pendente (RF-09, D-11)."""

    def test_lista_sessao_encerrada_com_participante_sem_registro(self):
        sessao = self.criar_sessao(self.agora - timedelta(hours=2), [PRESENTE, None])

        dados = self.consultar()

        self.assertEqual(dados['total'], 1)
        self.assertEqual(dados['por_tipo'], {'PRESENCA_PENDENTE': 1, 'RELATORIO_PENDENTE': 0})
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
        self.assertEqual(dados['por_tipo'], {'PRESENCA_PENDENTE': 0, 'RELATORIO_PENDENTE': 0})

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
        self.assertEqual(
            [tipo['valor'] for tipo in dados['tipos']], ['PRESENCA_PENDENTE', 'RELATORIO_PENDENTE']
        )

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


class PendenciasDeRelatorioTests(BasePendenciasTests):
    """Sessões de Treino realizadas sem relatório finalizado também são pendências (RF-09, D-11)."""

    def realizada(self, presencas=(PRESENTE,), servico=None, fim=None):
        sessao = self.criar_sessao(fim or self.agora - timedelta(hours=2), list(presencas), Sessao.Status.REALIZADA)
        if servico is not None:
            sessao.servico = servico
            sessao.save()
        return sessao

    def itens_de_relatorio(self, dados):
        return [item for item in dados['itens'] if item['tipo'] == 'RELATORIO_PENDENTE']

    def test_sessao_de_treino_realizada_sem_relatorio_e_pendente(self):
        sessao = self.realizada()

        dados = self.consultar()

        self.assertEqual(dados['por_tipo'], {'PRESENCA_PENDENTE': 0, 'RELATORIO_PENDENTE': 1})
        item = dados['itens'][0]
        self.assertEqual(item['tipo'], 'RELATORIO_PENDENTE')
        self.assertEqual(item['motivo'], 'Relatório de treino ainda não criado.')
        self.assertEqual(item['sessao']['id'], sessao.pk)
        self.assertEqual(item['responsavel'], {'id': self.treinador.pk, 'nome': 'Carla Dias'})
        self.assertEqual(item['detalhe'], f'/api/sessoes/{sessao.pk}/relatorio/')

    def test_relatorio_em_rascunho_e_pendente(self):
        sessao = self.realizada()
        RelatorioTreino.objects.create(sessao=sessao, objetivo='Rascunho')

        item = self.itens_de_relatorio(self.consultar())[0]

        self.assertEqual(item['motivo'], 'Relatório de treino em rascunho, ainda não finalizado.')

    def test_relatorio_finalizado_nao_e_pendente(self):
        sessao = self.realizada()
        RelatorioTreino.objects.create(sessao=sessao, status=RelatorioTreino.Status.FINALIZADO)

        self.assertEqual(self.consultar()['total'], 0)

    def test_so_sessoes_de_treino_realizadas_entram(self):
        fisio = Servico.objects.create(nome='Fisioterapia', categoria=Servico.Categoria.FISIOTERAPIA)
        self.realizada(servico=fisio)
        fim = self.agora - timedelta(hours=2)
        for status in (Sessao.Status.AGENDADA, Sessao.Status.NAO_REALIZADA, Sessao.Status.CANCELADA):
            self.criar_sessao(fim, [PRESENTE], status)

        self.assertEqual(self.itens_de_relatorio(self.consultar()), [])

    def test_mesma_sessao_pode_ter_as_duas_pendencias(self):
        sessao = self.realizada(presencas=[None])

        dados = self.consultar()

        self.assertEqual([item['tipo'] for item in dados['itens']], ['PRESENCA_PENDENTE', 'RELATORIO_PENDENTE'])
        self.assertEqual({item['sessao']['id'] for item in dados['itens']}, {sessao.pk})
        self.assertEqual(dados['total'], 2)

    def test_filtro_por_tipo_mantem_o_total_geral(self):
        self.criar_sessao(self.agora - timedelta(days=1), [None])
        relatorio = self.realizada()

        dados = self.consultar(tipo='RELATORIO_PENDENTE')

        self.assertEqual([item['sessao']['id'] for item in dados['itens']], [relatorio.pk])
        self.assertEqual(dados['total'], 2)

    def test_itens_dos_dois_tipos_seguem_a_ordem_de_encerramento(self):
        recente = self.realizada(fim=self.agora - timedelta(hours=1))
        antiga = self.criar_sessao(self.agora - timedelta(days=2), [None])

        self.assertEqual(self.ids(self.consultar()), [antiga.pk, recente.pk])

    def test_atalho_abre_o_relatorio_mas_nao_permite_ao_administrador_editar(self):
        sessao = self.realizada()
        RelatorioTreino.objects.create(sessao=sessao, objetivo='Rascunho')
        detalhe = self.itens_de_relatorio(self.consultar())[0]['detalhe']

        self.assertEqual(self.client.get(detalhe).status_code, 200)
        self.assertEqual(self.client.patch(detalhe, {'local': 'Sala 1'}, format='json').status_code, 403)


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
