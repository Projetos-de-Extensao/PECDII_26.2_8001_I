from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from app.models import Servico


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
