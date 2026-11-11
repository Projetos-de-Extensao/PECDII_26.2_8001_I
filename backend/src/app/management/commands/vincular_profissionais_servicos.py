import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.models import ProfissionalServico, Servico, Usuario


class Command(BaseCommand):
    """Cria vínculos profissionais-serviços a partir de um mapeamento explícito."""

    help = (
        'Vincula profissionais a serviços usando um CSV com as colunas '
        'email,servico. Por padrão, apenas mostra uma prévia.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            required=True,
            help='Caminho para CSV UTF-8 com cabeçalho email,servico.',
        )
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Grava os vínculos. Sem esta opção, o comando só mostra uma prévia.',
        )

    def handle(self, *args, **options):
        caminho = Path(options['arquivo']).expanduser()
        try:
            with caminho.open(encoding='utf-8-sig', newline='') as arquivo:
                leitor = csv.DictReader(arquivo)
                cabecalho = set(leitor.fieldnames or [])
                if not {'email', 'servico'}.issubset(cabecalho):
                    raise CommandError('O CSV precisa ter as colunas email,servico.')
                linhas = list(enumerate(leitor, start=2))
        except OSError as erro:
            raise CommandError(f'Não foi possível abrir {caminho}: {erro}') from erro

        pares = []
        pares_vistos = set()
        for numero_linha, linha in linhas:
            email = (linha.get('email') or '').strip()
            nome_servico = (linha.get('servico') or '').strip()
            if not email and not nome_servico:
                continue
            if not email or not nome_servico:
                raise CommandError(
                    f'Linha {numero_linha}: informe email e servico.'
                )

            try:
                profissional = Usuario.objects.get(email__iexact=email)
            except Usuario.DoesNotExist as erro:
                raise CommandError(
                    f'Linha {numero_linha}: profissional com e-mail {email!r} não encontrado.'
                ) from erro
            except Usuario.MultipleObjectsReturned as erro:
                raise CommandError(
                    f'Linha {numero_linha}: o e-mail {email!r} corresponde a mais de um usuário.'
                ) from erro

            if profissional.perfil not in Usuario.PERFIS_PROFISSIONAIS:
                raise CommandError(
                    f'Linha {numero_linha}: {profissional.nome} não tem perfil de profissional atendente.'
                )

            try:
                servico = Servico.objects.get(nome__iexact=nome_servico)
            except Servico.DoesNotExist as erro:
                raise CommandError(
                    f'Linha {numero_linha}: serviço {nome_servico!r} não encontrado.'
                ) from erro
            except Servico.MultipleObjectsReturned as erro:
                raise CommandError(
                    f'Linha {numero_linha}: o nome {nome_servico!r} corresponde a mais de um serviço.'
                ) from erro

            chave = (profissional.pk, servico.pk)
            if chave in pares_vistos:
                raise CommandError(
                    f'Linha {numero_linha}: vínculo duplicado para {profissional.nome} — {servico.nome}.'
                )
            pares_vistos.add(chave)
            pares.append((profissional, servico))

        if not pares:
            raise CommandError('O CSV não contém vínculos para processar.')

        novos = []
        for profissional, servico in pares:
            existe = ProfissionalServico.objects.filter(
                profissional=profissional,
                servico=servico,
            ).exists()
            if existe:
                self.stdout.write(f'Já vinculado: {profissional.nome} — {servico.nome}')
            else:
                novos.append((profissional, servico))
                self.stdout.write(f'Novo vínculo: {profissional.nome} — {servico.nome}')

        if not options['aplicar']:
            self.stdout.write(self.style.WARNING(
                f'Prévia: {len(novos)} vínculo(s) novo(s). Nada foi gravado; use --aplicar para confirmar.'
            ))
            return

        with transaction.atomic():
            for profissional, servico in novos:
                ProfissionalServico.objects.get_or_create(
                    profissional=profissional,
                    servico=servico,
                )

        self.stdout.write(self.style.SUCCESS(f'Vínculos criados: {len(novos)}'))
