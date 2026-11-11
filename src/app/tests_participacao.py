from datetime import datetime, timedelta, timezone as timezone_utc

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from app.admin import ParticipacaoInline, SessaoAdmin
from app.models import Aluno, Participacao, Servico, Sessao, Usuario


class BaseParticipacaoTests(TestCase):
    """Cria um treinador, um serviço, uma sessão e dois alunos."""

    def setUp(self):
        self.treinador = self.criar_usuario('treinador-participacao', Usuario.Perfil.TREINADOR)
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.inicio = datetime(2026, 11, 16, 9, tzinfo=timezone_utc.utc)
        self.sessao = Sessao.objects.create(
            servico=self.servico,
            profissional=self.treinador,
            inicio=self.inicio,
            fim=self.inicio + timedelta(hours=1),
        )
        self.ana = Aluno.objects.create(nome='Ana Lima', data_nascimento='2010-03-01')
        self.bruno = Aluno.objects.create(nome='Bruno Costa', data_nascimento='2011-07-15')

    def criar_usuario(self, login, perfil):
        conta = get_user_model().objects.create_user(username=login)
        return Usuario.objects.create(conta=conta, nome=login, email=f'{login}@example.com', perfil=perfil)


class ParticipacaoModelTests(BaseParticipacaoTests):
    """Verifica as regras da tabela participacao descritas no DER."""

    def test_participacao_comeca_sem_presenca_registrada(self):
        participacao = Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        self.assertIsNone(participacao.situacao_presenca)

    def test_sessao_pode_ter_varios_alunos(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)
        Participacao.objects.create(sessao=self.sessao, aluno=self.bruno)

        self.assertEqual(self.sessao.participacoes.count(), 2)

    def test_presenca_aceita_presente_e_falta(self):
        presente = Participacao.objects.create(
            sessao=self.sessao, aluno=self.ana, situacao_presenca=Participacao.SituacaoPresenca.PRESENTE
        )
        falta = Participacao.objects.create(
            sessao=self.sessao, aluno=self.bruno, situacao_presenca=Participacao.SituacaoPresenca.FALTA
        )

        self.assertEqual(presente.situacao_presenca, 'PRESENTE')
        self.assertEqual(falta.situacao_presenca, 'FALTA')

    def test_aluno_repetido_na_sessao_e_rejeitado_na_validacao(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        with self.assertRaises(ValidationError) as contexto:
            Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        self.assertIn('Este aluno já participa desta sessão.', contexto.exception.messages)

    def test_aluno_repetido_na_sessao_e_barrado_pelo_banco(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        # bulk_create não chama save(), então só a restrição do banco impede a duplicidade.
        with self.assertRaises(IntegrityError), transaction.atomic():
            Participacao.objects.bulk_create([Participacao(sessao=self.sessao, aluno=self.ana)])

    def test_presenca_fora_da_lista_e_rejeitada_na_validacao(self):
        with self.assertRaises(ValidationError) as contexto:
            Participacao.objects.create(sessao=self.sessao, aluno=self.ana, situacao_presenca='ATRASADO')

        self.assertIn('situacao_presenca', contexto.exception.message_dict)

    def test_presenca_fora_da_lista_e_barrada_pelo_banco(self):
        participacao = Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Participacao.objects.filter(pk=participacao.pk).update(situacao_presenca='ATRASADO')

    def test_remover_sessao_remove_suas_participacoes(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        self.sessao.delete()

        self.assertFalse(Participacao.objects.exists())
        self.assertTrue(Aluno.objects.filter(pk=self.ana.pk).exists())

    def test_aluno_com_participacao_nao_pode_ser_removido(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        with self.assertRaises(ProtectedError):
            self.ana.delete()

    def test_servico_com_sessao_nao_pode_ser_removido(self):
        with self.assertRaises(ProtectedError):
            self.servico.delete()

    def test_sessao_antiga_sem_servico_continua_valida(self):
        sessao = Sessao.objects.create(
            profissional=self.treinador,
            inicio=self.inicio + timedelta(days=1),
            fim=self.inicio + timedelta(days=1, hours=1),
        )

        self.assertIsNone(sessao.servico)


class RemocaoComParticipacaoApiTests(BaseParticipacaoTests):
    """A API recusa com 409, e não com 500, remoções que apagariam histórico."""

    def setUp(self):
        super().setUp()
        self.admin = self.criar_usuario('admin-participacao', Usuario.Perfil.ADMINISTRADOR)
        self.client = APIClient()
        self.client.force_authenticate(self.admin.conta)

    def test_remover_aluno_com_participacao_retorna_409(self):
        Participacao.objects.create(sessao=self.sessao, aluno=self.ana)

        response = self.client.delete(f'/api/alunos/{self.ana.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data['detail'],
            'Este aluno participa de sessões. Remova-o das sessões antes de excluir o cadastro.',
        )
        self.assertTrue(Aluno.objects.filter(pk=self.ana.pk).exists())

    def test_remover_aluno_sem_participacao_continua_permitido(self):
        response = self.client.delete(f'/api/alunos/{self.bruno.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Aluno.objects.filter(pk=self.bruno.pk).exists())

    def test_remover_servico_com_sessao_retorna_409(self):
        response = self.client.delete(f'/api/servicos/{self.servico.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.data['detail'],
            'Este serviço possui sessões agendadas ou realizadas e não pode ser excluído.',
        )
        self.assertTrue(Servico.objects.filter(pk=self.servico.pk).exists())

    def test_remover_servico_sem_sessao_continua_permitido(self):
        avulso = Servico.objects.create(nome='Nutrição esportiva', categoria=Servico.Categoria.NUTRICAO)

        response = self.client.delete(f'/api/servicos/{avulso.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Servico.objects.filter(pk=avulso.pk).exists())


class ParticipacaoAdminTests(TestCase):
    """Os participantes aparecem dentro da sessão no Django Admin."""

    def test_participantes_aparecem_no_admin_da_sessao(self):
        self.assertIn(ParticipacaoInline, SessaoAdmin.inlines)
        self.assertIsInstance(admin.site._registry[Sessao], SessaoAdmin)

    def test_admin_limita_os_participantes_a_capacidade_da_sessao(self):
        self.assertEqual(ParticipacaoInline.max_num, 6)
