from datetime import datetime, timedelta, timezone as timezone_utc
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from app.models import Aluno, Participacao, Servico, Sessao, Usuario

INICIO = datetime(2026, 11, 16, 9, tzinfo=timezone_utc.utc)


def criar_usuario(login, perfil):
    conta = get_user_model().objects.create_user(username=login)
    return Usuario.objects.create(conta=conta, nome=login, email=f'{login}@example.com', perfil=perfil)


def cliente(usuario):
    client = APIClient()
    client.force_authenticate(usuario.conta)
    return client


class BaseSessaoTests(TestCase):
    """Sessão de Treino com dois participantes, sob responsabilidade de um Treinador."""

    def setUp(self):
        self.admin = criar_usuario('admin-presenca', Usuario.Perfil.ADMINISTRADOR)
        self.responsavel = criar_usuario('treinador-responsavel', Usuario.Perfil.TREINADOR)
        self.outro_treinador = criar_usuario('outro-treinador', Usuario.Perfil.TREINADOR)
        self.fisio = criar_usuario('fisio-presenca', Usuario.Perfil.PROFISSIONAL_SAUDE)
        servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.sessao = Sessao.objects.create(
            titulo='Treino de força',
            servico=servico,
            profissional=self.responsavel,
            inicio=INICIO,
            fim=INICIO + timedelta(hours=1),
        )
        self.ana = Aluno.objects.create(nome='Ana Lima', data_nascimento='2010-03-01')
        self.bruno = Aluno.objects.create(nome='Bruno Costa', data_nascimento='2011-07-15')
        self.fora = Aluno.objects.create(nome='Carla Souza', data_nascimento='2012-01-20')
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)
        Participacao.objects.create(sessao=self.sessao, aluno=self.bruno)
        self.url_presencas = f'/api/sessoes/{self.sessao.pk}/presencas/'
        self.url_sessao = f'/api/sessoes/{self.sessao.pk}/'

    def presenca_de(self, aluno):
        return Participacao.objects.get(sessao=self.sessao, aluno=aluno).situacao_presenca


class RegistroPresencaTests(BaseSessaoTests):
    """PATCH /api/sessoes/{id}/presencas/ registra presença ou falta (RF-06, UC-06)."""

    def test_responsavel_registra_presenca_e_falta(self):
        response = cliente(self.responsavel).patch(
            self.url_presencas,
            {'presencas': [
                {'aluno': self.ana.pk, 'situacao': 'PRESENTE'},
                {'aluno': self.bruno.pk, 'situacao': 'FALTA'},
            ]},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['presencas'],
            [
                {'aluno': self.ana.pk, 'situacao_presenca': 'PRESENTE'},
                {'aluno': self.bruno.pk, 'situacao_presenca': 'FALTA'},
            ],
        )
        self.assertEqual(self.presenca_de(self.ana), 'PRESENTE')
        self.assertEqual(self.presenca_de(self.bruno), 'FALTA')

    def test_registro_parcial_mantem_os_demais_sem_presenca(self):
        response = cliente(self.responsavel).patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.presenca_de(self.ana), 'PRESENTE')
        self.assertIsNone(self.presenca_de(self.bruno))

    def test_responsavel_corrige_presenca_ja_registrada(self):
        client = cliente(self.responsavel)
        client.patch(self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'FALTA'}]}, format='json')

        response = client.patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.presenca_de(self.ana), 'PRESENTE')

    def test_consulta_da_sessao_mostra_a_presenca(self):
        cliente(self.responsavel).patch(
            self.url_presencas, {'presencas': [{'aluno': self.bruno.pk, 'situacao': 'FALTA'}]}, format='json'
        )

        response = cliente(self.outro_treinador).get(self.url_sessao)

        self.assertEqual(response.status_code, 200)
        self.assertIn({'aluno': self.bruno.pk, 'situacao_presenca': 'FALTA'}, response.data['presencas'])
        self.assertIn({'aluno': self.ana.pk, 'situacao_presenca': None}, response.data['presencas'])

    def test_outro_profissional_nao_registra_presenca(self):
        for usuario in (self.outro_treinador, self.fisio):
            response = cliente(usuario).patch(
                self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
            )

            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.data['detail'], 'Apenas o profissional responsável pela sessão registra presença ou falta.'
            )
        self.assertIsNone(self.presenca_de(self.ana))

    def test_administrador_nao_registra_presenca(self):
        response = cliente(self.admin).patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
        )

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.presenca_de(self.ana))

    def test_sem_autenticacao_e_recusado(self):
        response = APIClient().patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
        )

        self.assertEqual(response.status_code, 401)

    def test_aluno_fora_da_sessao_e_recusado_sem_gravar_nada(self):
        response = cliente(self.responsavel).patch(
            self.url_presencas,
            {'presencas': [
                {'aluno': self.ana.pk, 'situacao': 'PRESENTE'},
                {'aluno': self.fora.pk, 'situacao': 'PRESENTE'},
            ]},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['presencas'], [f'Aluno(s) que não participam desta sessão: {self.fora.pk}.']
        )
        self.assertIsNone(self.presenca_de(self.ana))

    def test_situacao_invalida_e_recusada(self):
        response = cliente(self.responsavel).patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'ATRASADO'}]}, format='json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['presencas'][0]['situacao'], ['Informe PRESENTE ou FALTA.'])
        self.assertIsNone(self.presenca_de(self.ana))

    def test_aluno_repetido_e_recusado(self):
        response = cliente(self.responsavel).patch(
            self.url_presencas,
            {'presencas': [
                {'aluno': self.ana.pk, 'situacao': 'PRESENTE'},
                {'aluno': self.ana.pk, 'situacao': 'FALTA'},
            ]},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['presencas'], ['O mesmo aluno foi informado mais de uma vez.'])

    def test_lista_vazia_e_recusada(self):
        response = cliente(self.responsavel).patch(self.url_presencas, {'presencas': []}, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('presencas', response.data)

    def test_sessao_cancelada_nao_recebe_presenca(self):
        self.sessao.status = Sessao.Status.CANCELADA
        self.sessao.save()

        response = cliente(self.responsavel).patch(
            self.url_presencas, {'presencas': [{'aluno': self.ana.pk, 'situacao': 'PRESENTE'}]}, format='json'
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['detail'], 'Sessão cancelada não recebe registro de presença ou falta.')
        self.assertIsNone(self.presenca_de(self.ana))

    def test_falha_no_meio_do_registro_desfaz_tudo(self):
        save_original = Participacao.save
        chamadas = []

        def falhar_na_segunda(participacao, *args, **kwargs):
            chamadas.append(participacao)
            if len(chamadas) == 2:
                raise IntegrityError('falha simulada')
            return save_original(participacao, *args, **kwargs)

        client = cliente(self.responsavel)
        client.raise_request_exception = False
        with mock.patch.object(Participacao, 'save', falhar_na_segunda):
            response = client.patch(
                self.url_presencas,
                {'presencas': [
                    {'aluno': self.ana.pk, 'situacao': 'PRESENTE'},
                    {'aluno': self.bruno.pk, 'situacao': 'FALTA'},
                ]},
                format='json',
            )

        self.assertEqual(response.status_code, 500)
        self.assertIsNone(self.presenca_de(self.ana))
        self.assertIsNone(self.presenca_de(self.bruno))


class AlteracaoSessaoTests(BaseSessaoTests):
    """Só o responsável e o Administrador alteram a sessão; só o Administrador remove (RN-05, RF-10)."""

    def test_outro_profissional_nao_altera_a_sessao(self):
        for usuario in (self.outro_treinador, self.fisio):
            response = cliente(usuario).patch(self.url_sessao, {'status': 'REALIZADA'}, format='json')

            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.data['detail'],
                'Apenas o profissional responsável ou o Administrador pode alterar esta sessão.',
            )
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.status, Sessao.Status.AGENDADA)

    def test_responsavel_registra_que_a_sessao_foi_ministrada(self):
        response = cliente(self.responsavel).patch(
            self.url_sessao, {'status': 'REALIZADA', 'observacoes': 'Turma completa.'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.status, Sessao.Status.REALIZADA)
        self.assertEqual(self.sessao.observacoes, 'Turma completa.')

    def test_responsavel_nao_altera_horario_nem_outros_campos(self):
        novo_inicio = INICIO + timedelta(days=1)
        response = cliente(self.responsavel).patch(
            self.url_sessao,
            {'inicio': novo_inicio.isoformat(), 'fim': (novo_inicio + timedelta(hours=1)).isoformat()},
            format='json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data['detail'], 'O profissional responsável altera apenas a situação e as observações da sessão.'
        )
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.inicio, INICIO)

    def test_responsavel_pode_reenviar_campos_sem_mudar_o_valor(self):
        response = cliente(self.responsavel).patch(
            self.url_sessao, {'titulo': 'Treino de força', 'status': 'NAO_REALIZADA'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.status, Sessao.Status.NAO_REALIZADA)

    def test_administrador_altera_a_sessao(self):
        response = cliente(self.admin).patch(self.url_sessao, {'titulo': 'Treino de potência'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.sessao.refresh_from_db()
        self.assertEqual(self.sessao.titulo, 'Treino de potência')

    def test_so_o_administrador_remove_a_sessao(self):
        recusado = cliente(self.responsavel).delete(self.url_sessao)
        self.assertEqual(recusado.status_code, 403)
        self.assertEqual(recusado.data['detail'], 'Apenas o perfil Administrador pode remover sessões.')
        self.assertTrue(Sessao.objects.filter(pk=self.sessao.pk).exists())

        removido = cliente(self.admin).delete(self.url_sessao)
        self.assertEqual(removido.status_code, 204)
        self.assertFalse(Sessao.objects.filter(pk=self.sessao.pk).exists())
