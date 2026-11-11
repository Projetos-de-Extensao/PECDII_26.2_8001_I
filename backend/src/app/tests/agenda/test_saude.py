from datetime import datetime, timedelta, timezone as timezone_utc

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from app.models import ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_para, criar_perfil


class AgendaProfissionalSaudeApiTests(TestCase):
    """A agenda de saúde mostra só atendimentos próprios de serviços vinculados."""

    def setUp(self):
        self.profissional = criar_perfil(Usuario.Perfil.PROFISSIONAL_SAUDE, 'saude-agenda')
        self.outro_profissional = criar_perfil(
            Usuario.Perfil.PROFISSIONAL_SAUDE, 'outra-saude-agenda'
        )
        self.servico_vinculado = self.criar_servico(
            'Fisioterapia esportiva', Servico.Categoria.FISIOTERAPIA
        )
        self.servico_nao_vinculado = self.criar_servico(
            'Nutrição esportiva', Servico.Categoria.NUTRICAO
        )
        self.servico_treino = self.criar_servico(
            'Treino funcional', Servico.Categoria.TREINO
        )
        ProfissionalServico.objects.create(
            profissional=self.profissional,
            servico=self.servico_vinculado,
        )
        ProfissionalServico.objects.create(
            profissional=self.outro_profissional,
            servico=self.servico_nao_vinculado,
        )
        ProfissionalServico.objects.create(
            profissional=self.outro_profissional,
            servico=self.servico_vinculado,
        )
        ProfissionalServico.objects.create(
            profissional=self.profissional,
            servico=self.servico_treino,
        )

        self.client = cliente_para(self.profissional)
        self.base = datetime(2026, 11, 16, 9, tzinfo=timezone_utc.utc)

    def criar_servico(self, nome, categoria):
        return Servico.objects.create(nome=nome, categoria=categoria)

    def criar_sessao(self, titulo, profissional, servico, inicio, duracao=timedelta(minutes=30)):
        return Sessao.objects.create(
            titulo=titulo,
            tipo=Sessao.Tipo.AVALIACAO,
            profissional=profissional,
            servico=servico,
            inicio=inicio,
            fim=inicio + duracao,
        )

    def test_lista_restringe_a_propria_agenda_e_servicos_de_saude_vinculados(self):
        permitida = self.criar_sessao(
            'Consulta permitida', self.profissional, self.servico_vinculado, self.base
        )
        self.criar_sessao(
            'Serviço sem vínculo', self.profissional, self.servico_nao_vinculado,
            self.base + timedelta(hours=1),
        )
        sessao_de_terceiro = self.criar_sessao(
            'Agenda alheia', self.outro_profissional, self.servico_vinculado,
            self.base + timedelta(hours=2),
        )
        self.criar_sessao(
            'Treino', self.profissional, self.servico_treino,
            self.base + timedelta(hours=3),
        )

        resposta = self.client.get('/api/sessoes/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item['id'] for item in resposta.data], [permitida.pk])
        detalhe_alheio = self.client.get(f'/api/sessoes/{sessao_de_terceiro.pk}/')
        self.assertEqual(detalhe_alheio.status_code, 404)

    def test_profissional_de_saude_filtra_por_servico_vinculado_sem_ampliar_escopo(self):
        propria = self.criar_sessao(
            'Consulta própria', self.profissional, self.servico_vinculado, self.base
        )
        self.criar_sessao(
            'Consulta de outro profissional', self.outro_profissional,
            self.servico_vinculado, self.base + timedelta(hours=1),
        )

        resposta = self.client.get(
            '/api/sessoes/', {'servico': self.servico_vinculado.pk}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item['id'] for item in resposta.data], [propria.pk])

    def test_profissional_de_saude_nao_filtra_por_servico_sem_vinculo(self):
        resposta = self.client.get(
            '/api/sessoes/', {'servico': self.servico_nao_vinculado.pk}
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(
            resposta.data['detail'],
            'Só é possível filtrar por serviços vinculados ao seu perfil.',
        )

    def test_periodo_inclui_sessoes_que_cruzam_a_janela_em_ordem_cronologica(self):
        antes_que_cruza_inicio = self.criar_sessao(
            'Cruza o início', self.profissional, self.servico_vinculado,
            self.base - timedelta(minutes=15), duracao=timedelta(minutes=30),
        )
        no_periodo = self.criar_sessao(
            'Dentro do período', self.profissional, self.servico_vinculado,
            self.base + timedelta(hours=1),
        )
        self.criar_sessao(
            'Começa no fim', self.profissional, self.servico_vinculado,
            self.base + timedelta(hours=2),
        )
        self.criar_sessao(
            'Termina no início', self.profissional, self.servico_vinculado,
            self.base - timedelta(hours=1), duracao=timedelta(hours=1),
        )

        resposta = self.client.get(
            '/api/sessoes/',
            {
                'inicio': self.base.isoformat(),
                'fim': (self.base + timedelta(hours=2)).isoformat(),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [item['id'] for item in resposta.data],
            [antes_que_cruza_inicio.pk, no_periodo.pk],
        )

    def test_parametro_de_outro_profissional_nao_expande_a_consulta(self):
        propria = self.criar_sessao(
            'Consulta própria', self.profissional, self.servico_vinculado, self.base
        )
        self.criar_sessao(
            'Consulta alheia', self.outro_profissional, self.servico_vinculado,
            self.base + timedelta(hours=1),
        )

        resposta = self.client.get(
            '/api/sessoes/', {'profissional': self.outro_profissional.pk}
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item['id'] for item in resposta.data], [propria.pk])

    def test_lista_de_pendentes_tambem_respeita_o_escopo_do_profissional(self):
        limite = timezone.now() - timedelta(hours=1)
        propria = self.criar_sessao(
            'Pendente próprio', self.profissional, self.servico_vinculado,
            limite - timedelta(hours=1),
        )
        self.criar_sessao(
            'Pendente alheio', self.outro_profissional, self.servico_vinculado,
            limite - timedelta(minutes=30),
        )

        resposta = self.client.get('/api/sessoes/pendentes-status/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item['id'] for item in resposta.data], [propria.pk])

    def test_periodo_invalido_e_sem_autenticacao_sao_recusados(self):
        periodo_invalido = self.client.get(
            '/api/sessoes/',
            {
                'inicio': self.base.isoformat(),
                'fim': (self.base - timedelta(hours=1)).isoformat(),
            },
        )
        sem_autenticacao = APIClient().get('/api/sessoes/')

        self.assertEqual(periodo_invalido.status_code, 400)
        self.assertEqual(sem_autenticacao.status_code, 401)
