import threading
import time
from datetime import datetime, timedelta, timezone as timezone_utc
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from app.agendamento import CAPACIDADE_MAXIMA_SESSAO, RegraDeAgendamentoViolada, confirmar_sessao
from app.models import (
    Aluno,
    Disponibilidade,
    Participacao,
    ProfissionalServico,
    Servico,
    Sessao,
    Usuario,
)

INICIO = datetime(2026, 11, 16, 9, tzinfo=timezone_utc.utc)


def criar_usuario(login, perfil):
    conta = get_user_model().objects.create_user(username=login)
    return Usuario.objects.create(conta=conta, nome=login, email=f'{login}@example.com', perfil=perfil)


def criar_alunos(quantidade):
    return [
        Aluno.objects.create(nome=f'Aluno {numero:02d}', data_nascimento='2010-01-01')
        for numero in range(1, quantidade + 1)
    ]


class ConfirmacaoApiTests(TestCase):
    """POST /api/sessoes/ confirma a sessão com serviço, profissional, intervalo e participantes."""

    def setUp(self):
        self.admin = criar_usuario('admin-confirmacao', Usuario.Perfil.ADMINISTRADOR)
        self.treinador = criar_usuario('treinador-confirmacao', Usuario.Perfil.TREINADOR)
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=INICIO - timedelta(days=1),
            fim=INICIO + timedelta(days=1),
        )
        self.alunos = criar_alunos(CAPACIDADE_MAXIMA_SESSAO + 1)
        self.client = APIClient()
        self.client.force_authenticate(self.admin.conta)

    def dados(self, **extras):
        dados = {
            'titulo': 'Treino de força',
            'tipo': Sessao.Tipo.TREINAMENTO,
            'inicio': INICIO.isoformat(),
            'fim': (INICIO + timedelta(hours=1)).isoformat(),
            'servico': self.servico.pk,
            'profissional': self.treinador.pk,
            'participantes': [self.alunos[0].pk, self.alunos[1].pk],
        }
        dados.update(extras)
        return dados

    def test_administrador_confirma_sessao_com_participantes(self):
        response = self.client.post('/api/sessoes/', self.dados(), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['servico'], self.servico.pk)
        self.assertEqual(response.data['participantes'], [self.alunos[0].pk, self.alunos[1].pk])
        sessao = Sessao.objects.get(pk=response.data['id'])
        self.assertEqual(sessao.participacoes.count(), 2)
        self.assertTrue(all(p.situacao_presenca is None for p in sessao.participacoes.all()))

    def test_consulta_da_sessao_lista_os_participantes(self):
        criada = self.client.post('/api/sessoes/', self.dados(), format='json')

        response = self.client.get(f"/api/sessoes/{criada.data['id']}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['participantes'], [self.alunos[0].pk, self.alunos[1].pk])

    def test_sessao_com_seis_alunos_e_aceita(self):
        participantes = [aluno.pk for aluno in self.alunos[:CAPACIDADE_MAXIMA_SESSAO]]

        response = self.client.post('/api/sessoes/', self.dados(participantes=participantes), format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Participacao.objects.count(), CAPACIDADE_MAXIMA_SESSAO)

    def test_sessao_com_sete_alunos_e_recusada_sem_gravar_nada(self):
        participantes = [aluno.pk for aluno in self.alunos]

        response = self.client.post('/api/sessoes/', self.dados(participantes=participantes), format='json')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['regra'], 'RN-02')
        self.assertEqual(
            response.data['detail'],
            'Uma sessão pode ter no máximo 6 alunos; foram informados 7.',
        )
        self.assertFalse(Sessao.objects.exists())
        self.assertFalse(Participacao.objects.exists())

    def test_treinador_nao_confirma_agendamento(self):
        client = APIClient()
        client.force_authenticate(self.treinador.conta)

        response = client.post('/api/sessoes/', self.dados(), format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'Apenas o perfil Administrador pode confirmar agendamentos.')
        self.assertFalse(Sessao.objects.exists())

    def test_profissional_de_saude_nao_confirma_agendamento(self):
        fisio = criar_usuario('fisio-confirmacao', Usuario.Perfil.PROFISSIONAL_SAUDE)
        client = APIClient()
        client.force_authenticate(fisio.conta)

        response = client.post('/api/sessoes/', self.dados(), format='json')

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Sessao.objects.exists())

    def test_confirmacao_sem_autenticacao_e_recusada(self):
        response = APIClient().post('/api/sessoes/', self.dados(), format='json')

        self.assertEqual(response.status_code, 401)

    def test_servico_e_participantes_sao_obrigatorios(self):
        dados = self.dados()
        del dados['servico']
        del dados['participantes']

        response = self.client.post('/api/sessoes/', dados, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['servico'], ['Informe o serviço da sessão.'])
        self.assertEqual(response.data['participantes'], ['Informe ao menos um aluno participante.'])

    def test_lista_vazia_de_participantes_e_recusada(self):
        response = self.client.post('/api/sessoes/', self.dados(participantes=[]), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('participantes', response.data)

    def test_aluno_repetido_e_recusado(self):
        repetido = [self.alunos[0].pk, self.alunos[0].pk]

        response = self.client.post('/api/sessoes/', self.dados(participantes=repetido), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['participantes'], ['O mesmo aluno foi informado mais de uma vez.'])
        self.assertFalse(Sessao.objects.exists())

    def test_aluno_inexistente_e_recusado(self):
        response = self.client.post('/api/sessoes/', self.dados(participantes=[999999]), format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('participantes', response.data)
        self.assertFalse(Sessao.objects.exists())

    def test_participantes_nao_mudam_depois_da_confirmacao(self):
        criada = self.client.post('/api/sessoes/', self.dados(), format='json')

        response = self.client.patch(
            f"/api/sessoes/{criada.data['id']}/",
            {'participantes': [self.alunos[2].pk]},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['participantes'],
            ['Os participantes são definidos na confirmação e não podem ser alterados.'],
        )
        self.assertEqual(
            list(Participacao.objects.values_list('aluno_id', flat=True).order_by('aluno_id')),
            [self.alunos[0].pk, self.alunos[1].pk],
        )


class AtomicidadeConfirmacaoTests(TestCase):
    """Sessão e participantes são gravados por inteiro ou não são gravados (RN-06)."""

    def setUp(self):
        self.treinador = criar_usuario('treinador-atomicidade', Usuario.Perfil.TREINADOR)
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=INICIO - timedelta(days=1),
            fim=INICIO + timedelta(days=1),
        )
        self.alunos = criar_alunos(3)
        self.dados = {
            'titulo': 'Treino de força',
            'inicio': INICIO,
            'fim': INICIO + timedelta(hours=1),
            'servico': self.servico,
            'profissional': self.treinador,
        }

    def test_falha_no_meio_da_gravacao_desfaz_tudo(self):
        save_original = Participacao.save
        chamadas = []

        def falhar_no_segundo_participante(participacao, *args, **kwargs):
            chamadas.append(participacao)
            if len(chamadas) == 2:
                raise IntegrityError('falha simulada ao gravar o segundo participante')
            return save_original(participacao, *args, **kwargs)

        with mock.patch.object(Participacao, 'save', falhar_no_segundo_participante):
            with self.assertRaises(IntegrityError):
                confirmar_sessao(dict(self.dados), self.alunos)

        self.assertFalse(Sessao.objects.exists())
        self.assertFalse(Participacao.objects.exists())

    def test_regra_violada_nao_grava_sessao(self):
        def recusar(dados, alunos):
            raise RegraDeAgendamentoViolada('RN-01', 'O profissional já possui um compromisso neste horário.')

        with mock.patch('app.agendamento.validar_regras_da_agenda', recusar):
            with self.assertRaises(RegraDeAgendamentoViolada):
                confirmar_sessao(dict(self.dados), self.alunos)

        self.assertFalse(Sessao.objects.exists())
        self.assertFalse(Participacao.objects.exists())


class ConcorrenciaConfirmacaoTests(TransactionTestCase):
    """Duas confirmações simultâneas não validam a mesma agenda (RN-06, RNF-03).

    A validação de conflito abaixo é um substituto da regra da #98: ela lê a agenda,
    espera para alargar a janela de corrida e só então deixa gravar. Sem a transação
    serializada, as duas threads leriam a agenda vazia e gravariam duas sessões.
    """

    def setUp(self):
        self.treinador = criar_usuario('treinador-concorrencia', Usuario.Perfil.TREINADOR)
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        Disponibilidade.objects.create(
            profissional=self.treinador,
            inicio=INICIO - timedelta(days=1),
            fim=INICIO + timedelta(days=1),
        )
        self.alunos = criar_alunos(2)

    @staticmethod
    def recusar_profissional_ocupado(dados, alunos):
        ocupado = Sessao.objects.filter(
            profissional=dados['profissional'],
            inicio__lt=dados['fim'],
            fim__gt=dados['inicio'],
        ).exists()
        time.sleep(0.3)
        if ocupado:
            raise RegraDeAgendamentoViolada('RN-01', 'O profissional já possui um compromisso neste horário.')

    def confirmar_em_thread(self, aluno, resultados, largada):
        try:
            largada.wait()
            dados = {
                'titulo': f'Treino de {aluno.nome}',
                'inicio': INICIO,
                'fim': INICIO + timedelta(hours=1),
                'servico': self.servico,
                'profissional': self.treinador,
            }
            confirmar_sessao(dados, [aluno])
            resultados.append('confirmada')
        except RegraDeAgendamentoViolada as erro:
            resultados.append(erro.regra)
        except Exception as erro:  # noqa: BLE001 - o teste precisa ver qualquer outra falha
            resultados.append(repr(erro))
        finally:
            connection.close()

    def test_confirmacoes_simultaneas_nao_gravam_compromissos_sobrepostos(self):
        resultados = []
        largada = threading.Barrier(2)

        with mock.patch('app.agendamento.validar_regras_da_agenda', self.recusar_profissional_ocupado):
            threads = [
                threading.Thread(target=self.confirmar_em_thread, args=(aluno, resultados, largada))
                for aluno in self.alunos
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

        self.assertEqual(sorted(resultados), ['RN-01', 'confirmada'])
        self.assertEqual(Sessao.objects.count(), 1)
        self.assertEqual(Participacao.objects.count(), 1)
