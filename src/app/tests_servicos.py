from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.forms import modelform_factory
from django.test import TestCase
from django.utils import timezone

from app.admin import ProfissionalServicoInline
from app.models import ProfissionalServico, Servico, Sessao, Usuario


class ServicoModelTests(TestCase):
    """Verifica as regras do catálogo de serviços (issue #79, RF-02)."""

    def test_categorias_sao_as_quatro_do_cenario(self):
        self.assertEqual(
            Servico.Categoria.values,
            ['TREINO', 'FISIOTERAPIA', 'PSICOLOGIA', 'NUTRICAO'],
        )
        self.assertEqual(Servico.Categoria.NUTRICAO.label, 'Nutrição')

    def test_cria_servico_valido(self):
        servico = Servico(nome='Treino funcional', categoria=Servico.Categoria.TREINO)

        servico.full_clean()
        servico.save()

        self.assertEqual(Servico.objects.get().nome, 'Treino funcional')
        self.assertEqual(str(servico), 'Treino funcional')

    def test_categoria_fora_da_lista_e_rejeitada_na_validacao(self):
        servico = Servico(nome='Massagem', categoria='MASSAGEM')

        with self.assertRaises(ValidationError) as contexto:
            servico.full_clean()

        self.assertIn('categoria', contexto.exception.message_dict)

    def test_categoria_fora_da_lista_e_barrada_pelo_banco(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Servico.objects.create(nome='Massagem', categoria='MASSAGEM')

    def test_nome_repetido_e_rejeitado_na_validacao(self):
        Servico.objects.create(nome='Pilates', categoria=Servico.Categoria.FISIOTERAPIA)
        repetido = Servico(nome='Pilates', categoria=Servico.Categoria.TREINO)

        with self.assertRaises(ValidationError) as contexto:
            repetido.full_clean()

        self.assertEqual(
            contexto.exception.message_dict['nome'],
            ['Já existe um serviço com este nome.'],
        )

    def test_nome_repetido_e_barrado_pelo_banco(self):
        Servico.objects.create(nome='Pilates', categoria=Servico.Categoria.FISIOTERAPIA)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Servico.objects.create(nome='Pilates', categoria=Servico.Categoria.TREINO)

    def test_espacos_nas_pontas_nao_driblam_a_unicidade(self):
        Servico.objects.create(nome='Pilates', categoria=Servico.Categoria.FISIOTERAPIA)
        repetido = Servico(nome='  Pilates ', categoria=Servico.Categoria.TREINO)

        with self.assertRaises(ValidationError):
            repetido.full_clean()

    def test_nome_e_salvo_sem_espacos_nas_pontas(self):
        servico = Servico.objects.create(
            nome='  Consulta nutricional ',
            categoria=Servico.Categoria.NUTRICAO,
        )

        servico.refresh_from_db()
        self.assertEqual(servico.nome, 'Consulta nutricional')

    def test_nome_e_categoria_sao_obrigatorios(self):
        servico = Servico(nome='   ', categoria='')

        with self.assertRaises(ValidationError) as contexto:
            servico.full_clean()

        self.assertIn('nome', contexto.exception.message_dict)
        self.assertIn('categoria', contexto.exception.message_dict)

    def test_listagem_segue_ordem_alfabetica(self):
        Servico.objects.create(nome='Psicologia do esporte', categoria=Servico.Categoria.PSICOLOGIA)
        Servico.objects.create(nome='Fisioterapia esportiva', categoria=Servico.Categoria.FISIOTERAPIA)

        self.assertEqual(
            list(Servico.objects.values_list('nome', flat=True)),
            ['Fisioterapia esportiva', 'Psicologia do esporte'],
        )

    def test_servico_aparece_no_django_admin(self):
        self.assertTrue(admin.site.is_registered(Servico))


class ProfissionalServicoTests(TestCase):
    """Verifica o vínculo entre profissionais e serviços (issue #79, RN-04)."""

    def setUp(self):
        self.treino = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.fisio = Servico.objects.create(nome='Fisioterapia esportiva', categoria=Servico.Categoria.FISIOTERAPIA)
        self.treinador = self.criar_usuario('Bruno Costa', Usuario.Perfil.TREINADOR)
        self.fisioterapeuta = self.criar_usuario('Carla Dias', Usuario.Perfil.PROFISSIONAL_SAUDE)
        self.administrador = self.criar_usuario('Ana Souza', Usuario.Perfil.ADMINISTRADOR)

    def criar_usuario(self, nome, perfil):
        login = nome.lower().replace(' ', '.')
        return Usuario.objects.create(
            # Sem senha: nenhum destes testes faz login, e gerar o hash deixava a suíte lenta.
            conta=get_user_model().objects.create_user(username=login),
            nome=nome,
            email=f'{login}@example.com',
            perfil=perfil,
        )

    def test_treinador_e_profissional_de_saude_podem_ser_vinculados(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)
        ProfissionalServico.objects.create(profissional=self.fisioterapeuta, servico=self.fisio)

        self.assertEqual(ProfissionalServico.objects.count(), 2)

    def test_profissional_pode_atender_varios_servicos(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.fisio)

        self.assertQuerySetEqual(
            Servico.objects.filter(vinculos__profissional=self.treinador),
            [self.fisio, self.treino],
        )

    def test_servico_pode_ter_varios_profissionais(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.fisio)
        ProfissionalServico.objects.create(profissional=self.fisioterapeuta, servico=self.fisio)

        self.assertQuerySetEqual(
            Usuario.objects.filter(vinculos__servico=self.fisio),
            [self.treinador, self.fisioterapeuta],
        )

    def test_administrador_nao_pode_ser_vinculado(self):
        with self.assertRaises(ValidationError) as contexto:
            ProfissionalServico.objects.create(profissional=self.administrador, servico=self.treino)

        self.assertEqual(
            contexto.exception.message_dict['profissional'],
            ['Apenas Treinador ou Profissional de Saúde podem ser vinculados a um serviço.'],
        )
        self.assertFalse(ProfissionalServico.objects.exists())

    def test_vinculo_repetido_e_rejeitado_na_validacao(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)

        with self.assertRaises(ValidationError) as contexto:
            ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)

        self.assertIn(
            'Este profissional já está vinculado a este serviço.',
            contexto.exception.messages,
        )

    def test_vinculo_repetido_e_barrado_pelo_banco(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)

        # bulk_create não passa pelo save(), então quem barra aqui é a restrição do banco.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProfissionalServico.objects.bulk_create(
                    [ProfissionalServico(profissional=self.treinador, servico=self.treino)]
                )

    def test_remover_servico_remove_seus_vinculos(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)

        self.treino.delete()

        self.assertFalse(ProfissionalServico.objects.exists())
        self.assertTrue(Usuario.objects.filter(pk=self.treinador.pk).exists())

    def test_remover_profissional_remove_seus_vinculos(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.treino)

        self.treinador.delete()

        self.assertFalse(ProfissionalServico.objects.exists())
        self.assertTrue(Servico.objects.filter(pk=self.treino.pk).exists())

    def test_admin_oferece_apenas_perfis_profissionais(self):
        formulario = modelform_factory(ProfissionalServico, fields=['profissional', 'servico'])()
        opcoes = formulario.fields['profissional'].queryset

        self.assertIn(self.treinador, opcoes)
        self.assertIn(self.fisioterapeuta, opcoes)
        self.assertNotIn(self.administrador, opcoes)

    def test_vinculos_aparecem_no_admin_do_servico(self):
        self.assertIn(ProfissionalServicoInline, admin.site.get_model_admin(Servico).inlines)

    def test_admin_conta_profissionais_numa_unica_consulta(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.fisio)
        ProfissionalServico.objects.create(profissional=self.fisioterapeuta, servico=self.fisio)
        servico_admin = admin.site.get_model_admin(Servico)

        with self.assertNumQueries(1):
            totais = {
                servico.nome: servico_admin.quantidade_de_profissionais(servico)
                for servico in servico_admin.get_queryset(request=None)
            }

        self.assertEqual(totais, {'Fisioterapia esportiva': 2, 'Treino funcional': 0})


class PerfilComVinculosTests(TestCase):
    """Quem atende serviços não pode virar Administrador sem antes perder os vínculos."""

    def setUp(self):
        self.servico = Servico.objects.create(nome='Treino funcional', categoria=Servico.Categoria.TREINO)
        self.treinador = Usuario.objects.create(
            conta=get_user_model().objects.create_user(username='bruno.costa'),
            nome='Bruno Costa',
            email='bruno.costa@example.com',
            perfil=Usuario.Perfil.TREINADOR,
        )

    def test_save_recusa_virar_administrador_com_vinculo(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR

        with self.assertRaises(ValidationError) as contexto:
            self.treinador.save()

        self.assertIn('perfil', contexto.exception.message_dict)
        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.TREINADOR)

    def test_validacao_do_admin_recusa_virar_administrador_com_vinculo(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR

        with self.assertRaises(ValidationError) as contexto:
            self.treinador.full_clean()

        self.assertEqual(
            contexto.exception.message_dict['perfil'],
            ['Este usuário atende serviços. Remova os vínculos antes de mudar o perfil para Administrador.'],
        )

    def test_sem_vinculo_o_perfil_pode_mudar(self):
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR
        self.treinador.save()

        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.ADMINISTRADOR)

    def test_troca_entre_perfis_profissionais_continua_livre(self):
        ProfissionalServico.objects.create(profissional=self.treinador, servico=self.servico)
        self.treinador.perfil = Usuario.Perfil.PROFISSIONAL_SAUDE
        self.treinador.save()

        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.PROFISSIONAL_SAUDE)


class PerfilComSessoesTests(TestCase):
    """Quem é responsável por sessões não pode virar Administrador (#88)."""

    def setUp(self):
        self.treinador = Usuario.objects.create(
            conta=get_user_model().objects.create_user(username='carla.dias'),
            nome='Carla Dias',
            email='carla.dias@example.com',
            perfil=Usuario.Perfil.TREINADOR,
        )
        agora = timezone.now()
        Sessao.objects.create(inicio=agora, fim=agora + timedelta(hours=1), profissional=self.treinador)

    def test_save_recusa_virar_administrador_com_sessoes(self):
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR

        with self.assertRaises(ValidationError) as contexto:
            self.treinador.save()

        self.assertIn('perfil', contexto.exception.message_dict)
        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.TREINADOR)

    def test_validacao_do_admin_recusa_virar_administrador_com_sessoes(self):
        self.treinador.perfil = Usuario.Perfil.ADMINISTRADOR

        with self.assertRaises(ValidationError) as contexto:
            self.treinador.full_clean()

        self.assertEqual(
            contexto.exception.message_dict['perfil'],
            [
                'Este usuário é responsável por sessões. Transfira as sessões para outro '
                'profissional antes de mudar o perfil para Administrador.'
            ],
        )

    def test_troca_entre_perfis_profissionais_com_sessoes_continua_livre(self):
        self.treinador.perfil = Usuario.Perfil.PROFISSIONAL_SAUDE
        self.treinador.save()

        self.treinador.refresh_from_db()
        self.assertEqual(self.treinador.perfil, Usuario.Perfil.PROFISSIONAL_SAUDE)
