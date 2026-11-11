from datetime import datetime, timedelta, timezone as timezone_utc

from django.test import TestCase

from app.models import ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_para, criar_perfil


class AgendaAdministradorETreinadorApiTests(TestCase):
    """Verifica escopo e filtros da agenda operacional e do Treinador."""

    def setUp(self):
        self.admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-agenda-95')
        self.treinador = criar_perfil(Usuario.Perfil.TREINADOR, 'treinador-agenda-95')
        self.outro_treinador = criar_perfil(
            Usuario.Perfil.TREINADOR, 'outro-treinador-agenda-95'
        )
        self.saude = criar_perfil(Usuario.Perfil.PROFISSIONAL_SAUDE, 'saude-agenda-95')

        self.treino = self.criar_servico('Treino agenda 95', Servico.Categoria.TREINO)
        self.fisioterapia = self.criar_servico(
            'Fisioterapia agenda 95', Servico.Categoria.FISIOTERAPIA
        )
        self.nutricao = self.criar_servico('Nutrição agenda 95', Servico.Categoria.NUTRICAO)
        for servico in (self.treino, self.fisioterapia):
            ProfissionalServico.objects.create(profissional=self.treinador, servico=servico)
        ProfissionalServico.objects.create(profissional=self.outro_treinador, servico=self.treino)
        ProfissionalServico.objects.create(profissional=self.saude, servico=self.nutricao)

        self.admin_client = cliente_para(self.admin)
        self.treinador_client = cliente_para(self.treinador)
        self.base = datetime(2026, 11, 16, 9, tzinfo=timezone_utc.utc)

        self.sessao_outro_treinador = self.criar_sessao(
            'Sessão de outro treinador', self.outro_treinador, self.treino,
            self.base,
        )
        self.sessao_treino = self.criar_sessao(
            'Treino', self.treinador, self.treino,
            self.base + timedelta(hours=1),
        )
        self.sessao_fisioterapia = self.criar_sessao(
            'Fisioterapia', self.treinador, self.fisioterapia,
            self.base + timedelta(hours=2),
        )
        self.sessao_sem_servico = self.criar_sessao(
            'Sessão antiga sem serviço', self.treinador, None,
            self.base + timedelta(hours=3),
        )
        self.sessao_servico_nao_vinculado = self.criar_sessao(
            'Serviço não vinculado', self.treinador, self.nutricao,
            self.base + timedelta(hours=4),
        )
        self.sessao_saude = self.criar_sessao(
            'Atendimento de saúde', self.saude, self.nutricao,
            self.base - timedelta(hours=1),
        )

    def criar_servico(self, nome, categoria):
        return Servico.objects.create(nome=nome, categoria=categoria)

    def criar_sessao(self, titulo, profissional, servico, inicio):
        return Sessao.objects.create(
            titulo=titulo,
            tipo=Sessao.Tipo.TREINAMENTO,
            profissional=profissional,
            servico=servico,
            inicio=inicio,
            fim=inicio + timedelta(minutes=30),
        )

    def test_administrador_consulta_toda_a_agenda_em_ordem_cronologica(self):
        resposta = self.admin_client.get('/api/sessoes/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [item['id'] for item in resposta.data],
            [
                self.sessao_saude.pk,
                self.sessao_outro_treinador.pk,
                self.sessao_treino.pk,
                self.sessao_fisioterapia.pk,
                self.sessao_sem_servico.pk,
                self.sessao_servico_nao_vinculado.pk,
            ],
        )

    def test_treinador_consulta_somente_suas_sessoes(self):
        resposta = self.treinador_client.get('/api/sessoes/')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [item['id'] for item in resposta.data],
            [
                self.sessao_treino.pk,
                self.sessao_fisioterapia.pk,
                self.sessao_sem_servico.pk,
                self.sessao_servico_nao_vinculado.pk,
            ],
        )
        self.assertEqual(
            self.treinador_client.get(f'/api/sessoes/{self.sessao_outro_treinador.pk}/').status_code,
            404,
        )

    def test_treinador_filtra_por_servico_vinculado_e_periodo(self):
        resposta = self.treinador_client.get(
            '/api/sessoes/',
            {
                'servico': self.fisioterapia.pk,
                'inicio': self.base.isoformat(),
                'fim': (self.base + timedelta(hours=3)).isoformat(),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([item['id'] for item in resposta.data], [self.sessao_fisioterapia.pk])

    def test_treinador_nao_filtra_por_servico_sem_vinculo(self):
        resposta = self.treinador_client.get(
            '/api/sessoes/', {'servico': self.nutricao.pk}
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(
            resposta.data['detail'],
            'Só é possível filtrar por serviços vinculados ao seu perfil.',
        )

    def test_administrador_pode_filtrar_agenda_por_servico_e_periodo(self):
        resposta = self.admin_client.get(
            '/api/sessoes/',
            {
                'servico': self.nutricao.pk,
                'inicio': self.base.isoformat(),
                'fim': (self.base + timedelta(hours=5)).isoformat(),
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [item['id'] for item in resposta.data],
            [self.sessao_servico_nao_vinculado.pk],
        )
