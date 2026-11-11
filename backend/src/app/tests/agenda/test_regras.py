from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from app.models import (
    Aluno,
    BloqueioAgenda,
    Disponibilidade,
    Participacao,
    ProfissionalServico,
    Servico,
    Sessao,
    Usuario,
)
from app.tests.helpers import cliente_para, criar_perfil


class RegrasDaAgendaApiTests(TestCase):
    """Valida RN-01, RN-03, RN-04 e RN-07 durante a confirmação transacional."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-regras')
        self.profissional = criar_perfil(Usuario.Perfil.PROFISSIONAL_SAUDE, 'profissional-regras')
        self.outro_profissional = criar_perfil(Usuario.Perfil.TREINADOR, 'outro-profissional-regras')
        self.servico = Servico.objects.create(
            nome='Fisioterapia de agenda',
            categoria=Servico.Categoria.FISIOTERAPIA,
        )
        self.servico_sem_vinculo = Servico.objects.create(
            nome='Nutrição de agenda',
            categoria=Servico.Categoria.NUTRICAO,
        )
        ProfissionalServico.objects.create(
            profissional=self.profissional,
            servico=self.servico,
        )
        ProfissionalServico.objects.create(
            profissional=self.outro_profissional,
            servico=self.servico,
        )
        self.aluno = Aluno.objects.create(nome='Aluno da agenda', data_nascimento='2000-01-01')
        self.outro_aluno = Aluno.objects.create(nome='Outro aluno', data_nascimento='2001-02-02')
        self.inicio = timezone.now() + timedelta(days=2)
        self.fim = self.inicio + timedelta(hours=8)
        self.disponibilizar(self.profissional)
        self.disponibilizar(self.outro_profissional)
        self.client = cliente_para(self.admin)

    def disponibilizar(self, profissional):
        Disponibilidade.objects.create(
            profissional=profissional,
            inicio=self.inicio,
            fim=self.fim,
        )

    def payload(self, **alteracoes):
        dados = {
            'titulo': 'Atendimento de agenda',
            'tipo': Sessao.Tipo.AVALIACAO,
            'servico': self.servico.pk,
            'profissional': self.profissional.pk,
            'inicio': (self.inicio + timedelta(hours=1)).isoformat(),
            'fim': (self.inicio + timedelta(hours=2)).isoformat(),
            'participantes': [self.aluno.pk],
        }
        dados.update(alteracoes)
        return dados

    def criar_sessao(self, *, profissional=None, aluno=None, inicio=None, fim=None, status=None):
        inicio = inicio or self.inicio + timedelta(hours=1)
        sessao = Sessao.objects.create(
            titulo='Sessão já confirmada',
            inicio=inicio,
            fim=fim or inicio + timedelta(hours=1),
            servico=self.servico,
            profissional=profissional or self.profissional,
            status=status or Sessao.Status.AGENDADA,
        )
        if aluno is not None:
            Participacao.objects.create(sessao=sessao, aluno=aluno)
        return sessao

    def assert_regra_recusada(self, response, regra):
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['regra'], regra)
        self.assertTrue(response.data['detail'])

    def test_servico_sem_vinculo_e_recusado_sem_gravar(self):
        response = self.client.post(
            '/api/sessoes/',
            self.payload(servico=self.servico_sem_vinculo.pk),
            format='json',
        )

        self.assert_regra_recusada(response, 'RN-04')
        self.assertFalse(Sessao.objects.exists())
        self.assertFalse(Participacao.objects.exists())

    def test_intervalo_fora_da_disponibilidade_e_recusado_sem_gravar(self):
        Disponibilidade.objects.filter(profissional=self.profissional).delete()
        Disponibilidade.objects.create(
            profissional=self.profissional,
            inicio=self.inicio,
            fim=self.inicio + timedelta(hours=1),
        )
        inicio_solicitado = self.inicio + timedelta(hours=2)

        response = self.client.post(
            '/api/sessoes/',
            self.payload(
                inicio=inicio_solicitado.isoformat(),
                fim=(inicio_solicitado + timedelta(hours=1)).isoformat(),
            ),
            format='json',
        )

        self.assert_regra_recusada(response, 'RN-03')
        self.assertIn('disponibilidade', response.data['detail'])
        self.assertFalse(Sessao.objects.exists())

    def test_bloqueio_parcial_e_recusado_sem_gravar(self):
        inicio_solicitado = self.inicio + timedelta(hours=1)
        BloqueioAgenda.objects.create(
            profissional=self.profissional,
            inicio=inicio_solicitado + timedelta(minutes=20),
            fim=inicio_solicitado + timedelta(minutes=30),
            motivo='Pausa',
        )

        response = self.client.post(
            '/api/sessoes/',
            self.payload(
                inicio=inicio_solicitado.isoformat(),
                fim=(inicio_solicitado + timedelta(hours=1)).isoformat(),
            ),
            format='json',
        )

        self.assert_regra_recusada(response, 'RN-03')
        self.assertIn('bloqueio', response.data['detail'])
        self.assertFalse(Sessao.objects.exists())

    def test_conflito_de_profissional_e_recusado(self):
        inicio_solicitado = self.inicio + timedelta(hours=1)
        self.criar_sessao(
            aluno=self.outro_aluno,
            inicio=inicio_solicitado + timedelta(minutes=30),
            fim=inicio_solicitado + timedelta(hours=2),
        )

        response = self.client.post(
            '/api/sessoes/',
            self.payload(inicio=inicio_solicitado.isoformat()),
            format='json',
        )

        self.assert_regra_recusada(response, 'RN-01')
        self.assertIn('profissional', response.data['detail'])
        self.assertEqual(Sessao.objects.count(), 1)

    def test_conflito_de_participante_e_recusado(self):
        inicio_solicitado = self.inicio + timedelta(hours=1)
        self.criar_sessao(
            profissional=self.outro_profissional,
            aluno=self.aluno,
            inicio=inicio_solicitado,
        )

        response = self.client.post(
            '/api/sessoes/',
            self.payload(inicio=(inicio_solicitado + timedelta(minutes=30)).isoformat()),
            format='json',
        )

        self.assert_regra_recusada(response, 'RN-07')
        self.assertIn('Aluno da agenda', response.data['detail'])
        self.assertEqual(Sessao.objects.count(), 1)

    def test_intervalos_contiguos_sao_aceitos_para_profissional_e_aluno(self):
        existente = self.criar_sessao(
            aluno=self.aluno,
            inicio=self.inicio + timedelta(hours=1),
            fim=self.inicio + timedelta(hours=2),
        )

        response = self.client.post(
            '/api/sessoes/',
            self.payload(
                inicio=existente.fim.isoformat(),
                fim=(existente.fim + timedelta(hours=1)).isoformat(),
            ),
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Sessao.objects.count(), 2)

    def test_sessoes_canceladas_nao_bloqueiam_profissional_nem_aluno(self):
        inicio_solicitado = self.inicio + timedelta(hours=1)
        self.criar_sessao(
            aluno=self.aluno,
            inicio=inicio_solicitado,
            status=Sessao.Status.CANCELADA,
        )

        response = self.client.post(
            '/api/sessoes/',
            self.payload(inicio=inicio_solicitado.isoformat()),
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Sessao.objects.count(), 2)

    def test_fim_igual_ao_inicio_e_recusado_sem_gravar(self):
        instante = self.inicio + timedelta(hours=1)

        response = self.client.post(
            '/api/sessoes/',
            self.payload(inicio=instante.isoformat(), fim=instante.isoformat()),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('fim', response.data)
        self.assertFalse(Sessao.objects.exists())
