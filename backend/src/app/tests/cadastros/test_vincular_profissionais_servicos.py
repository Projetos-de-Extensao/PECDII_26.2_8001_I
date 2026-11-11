import tempfile
from pathlib import Path

from django.core.management import call_command, CommandError
from django.test import TestCase

from app.models import ProfissionalServico, Servico, Usuario
from app.tests.helpers import criar_perfil


class VincularProfissionaisServicosCommandTests(TestCase):
    """O importador exige mapeamento explícito e oferece prévia sem gravar."""

    def setUp(self):
        self.profissional = criar_perfil(
            Usuario.Perfil.TREINADOR, 'treinador-importacao', nome='Treinador Importação',
        )
        self.servico = Servico.objects.create(
            nome='Treino individual', categoria=Servico.Categoria.TREINO,
        )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv_path = Path(self.temp.name) / 'habilitacoes.csv'
        self.csv_path.write_text(
            'email,servico\n'
            f'{self.profissional.email},{self.servico.nome}\n',
            encoding='utf-8',
        )

    def test_por_padrao_apenas_mostra_previa(self):
        call_command('vincular_profissionais_servicos', arquivo=str(self.csv_path))

        self.assertFalse(ProfissionalServico.objects.exists())

    def test_aplicar_grava_os_vinculos_mapeados(self):
        call_command(
            'vincular_profissionais_servicos', arquivo=str(self.csv_path), aplicar=True,
        )

        self.assertTrue(ProfissionalServico.objects.filter(
            profissional=self.profissional, servico=self.servico,
        ).exists())

    def test_nao_permite_mapear_usuario_administrador(self):
        admin = criar_perfil(Usuario.Perfil.ADMINISTRADOR, 'admin-importacao')
        self.csv_path.write_text(
            f'email,servico\n{admin.email},{self.servico.nome}\n',
            encoding='utf-8',
        )

        with self.assertRaises(CommandError):
            call_command('vincular_profissionais_servicos', arquivo=str(self.csv_path), aplicar=True)

        self.assertFalse(ProfissionalServico.objects.exists())
