from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from app.models import Aluno, Disponibilidade, ProfissionalServico, Servico, Sessao, Usuario
from app.tests.helpers import cliente_autenticado, cliente_para, criar_usuario


class SessaoApiTests(TestCase):
    """Verifica criação, pendências e atualização do status das sessões."""

    def setUp(self):
        self.client = cliente_autenticado(Usuario.Perfil.TREINADOR, 'teste-api-sessao')
        # Confirmar agendamento é exclusivo do Administrador (UC-05).
        self.admin_client = cliente_autenticado(Usuario.Perfil.ADMINISTRADOR, 'admin-api-sessao')
        self.profissional_conta = criar_usuario(Usuario.Perfil.TREINADOR, 'responsavel-sessao')
        self.profissional = self.profissional_conta.usuario
        # Só o responsável registra se a sessão foi ministrada (RN-05, RF-10).
        self.responsavel_client = cliente_para(self.profissional_conta)
        self.servico = Servico.objects.create(nome='Avaliação física', categoria=Servico.Categoria.TREINO)
        ProfissionalServico.objects.create(profissional=self.profissional, servico=self.servico)
        agora = timezone.now()
        Disponibilidade.objects.create(
            profissional=self.profissional,
            inicio=agora - timedelta(days=1),
            fim=agora + timedelta(days=365),
        )
        self.aluno = Aluno.objects.create(nome='Aluno da sessão', data_nascimento='2010-01-01')

    def criar_sessao(self, **overrides):
        agora = timezone.now()
        dados = {
            'titulo': 'Treino funcional',
            'tipo': Sessao.Tipo.TREINAMENTO,
            'inicio': agora - timedelta(hours=2),
            'fim': agora - timedelta(hours=1),
            'profissional': self.profissional,
        }
        dados.update(overrides)
        return Sessao.objects.create(**dados)

    def test_cria_sessao_com_profissional_tipo_e_descricao(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.admin_client.post(
            '/api/sessoes/',
            {
                'titulo': 'Avaliação inicial',
                'tipo': Sessao.Tipo.AVALIACAO,
                'descricao': 'Avaliação de mobilidade e força.',
                'inicio': inicio.isoformat(),
                'fim': (inicio + timedelta(minutes=60)).isoformat(),
                'servico': self.servico.pk,
                'profissional': self.profissional.pk,
                'participantes': [self.aluno.pk],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tipo'], Sessao.Tipo.AVALIACAO)
        self.assertEqual(response.data['descricao'], 'Avaliação de mobilidade e força.')
        self.assertEqual(response.data['profissional'], self.profissional.pk)

    def test_criacao_sem_profissional_e_rejeitada(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.admin_client.post(
            '/api/sessoes/',
            {
                'titulo': 'Treino funcional',
                'tipo': Sessao.Tipo.TREINAMENTO,
                'inicio': inicio.isoformat(),
                'fim': (inicio + timedelta(minutes=60)).isoformat(),
                'servico': self.servico.pk,
                'participantes': [self.aluno.pk],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('profissional', response.data)

    def test_fim_anterior_ao_inicio_e_rejeitado(self):
        inicio = timezone.now() + timedelta(days=1)
        response = self.admin_client.post(
            '/api/sessoes/',
            {
                'titulo': 'Treino funcional',
                'tipo': Sessao.Tipo.TREINAMENTO,
                'inicio': inicio.isoformat(),
                'fim': (inicio - timedelta(minutes=1)).isoformat(),
                'servico': self.servico.pk,
                'profissional': self.profissional.pk,
                'participantes': [self.aluno.pk],
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('fim', response.data)

    def test_lista_somente_sessoes_pendentes_com_mais_de_30_minutos(self):
        vencida = self.criar_sessao()
        recente = self.criar_sessao(
            titulo='Sessão recente',
            inicio=timezone.now() - timedelta(minutes=50),
            fim=timezone.now() - timedelta(minutes=20),
        )
        self.criar_sessao(
            titulo='Já realizada',
            status=Sessao.Status.REALIZADA,
        )

        response = self.responsavel_client.get('/api/sessoes/pendentes-status/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [vencida.pk])
        self.assertNotIn(recente.pk, [item['id'] for item in response.data])

    def test_atualiza_status_para_realizada_e_salva_observacoes(self):
        sessao = self.criar_sessao()

        response = self.responsavel_client.patch(
            f'/api/sessoes/{sessao.pk}/',
            {'status': Sessao.Status.REALIZADA, 'observacoes': 'Treino de força concluído.'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.REALIZADA)
        self.assertEqual(sessao.observacoes, 'Treino de força concluído.')

    def test_atualiza_status_para_nao_realizada(self):
        sessao = self.criar_sessao()

        response = self.responsavel_client.patch(
            f'/api/sessoes/{sessao.pk}/',
            {'status': Sessao.Status.NAO_REALIZADA},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.status, Sessao.Status.NAO_REALIZADA)
