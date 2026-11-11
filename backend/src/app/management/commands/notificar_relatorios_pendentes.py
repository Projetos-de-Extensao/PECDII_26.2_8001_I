from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from app.models import NotificacaoEmail, RelatorioTreino, Servico, Sessao, Usuario

# Tempo, depois do fim previsto da sessão, para lembrar o Treinador (RF-12).
HORAS_PARA_LEMBRAR = 24


class Command(BaseCommand):
    """Lembra o Treinador responsável de relatórios de treino ainda pendentes (RF-12)."""

    help = 'Envia um lembrete por e-mail quando o relatório de treino segue pendente 24 horas após a sessão.'

    def handle(self, *args, **options):
        limite = timezone.now() - timedelta(hours=HORAS_PARA_LEMBRAR)
        # Mesma regra da pendência de relatório (RF-09): só sessões de Treino marcadas como realizadas,
        # porque o relatório só pode ser criado depois disso. Atendimentos de saúde ficam de fora.
        sessoes = (
            Sessao.objects.filter(
                fim__lte=limite,
                status=Sessao.Status.REALIZADA,
                servico__categoria=Servico.Categoria.TREINO,
                profissional__perfil=Usuario.Perfil.TREINADOR,
            )
            .filter(
                Q(relatorio_treino__isnull=True)
                | Q(relatorio_treino__status=RelatorioTreino.Status.RASCUNHO)
            )
            .exclude(notificacoes__tipo=NotificacaoEmail.Tipo.RELATORIO_PENDENTE)
            .select_related('profissional')
        )

        enviados = 0
        for sessao in sessoes:
            treinador = sessao.profissional
            if not treinador.email:
                self.stderr.write(f'Sessão {sessao.pk}: Treinador sem e-mail; lembrete ignorado.')
                continue

            try:
                with transaction.atomic():
                    # O registro é gravado antes do envio. Se outra execução já gravou o mesmo aviso,
                    # a restrição única gera IntegrityError e este lembrete não é enviado de novo.
                    NotificacaoEmail.objects.create(
                        sessao=sessao,
                        tipo=NotificacaoEmail.Tipo.RELATORIO_PENDENTE,
                    )
                    send_mail(
                        subject=f'Relatório de treino pendente: {sessao.titulo}',
                        message=(
                            f'Olá, {treinador.nome}.\n\n'
                            f'O relatório da sessão "{sessao.titulo}", encerrada em '
                            f'{timezone.localtime(sessao.fim):%d/%m/%Y às %H:%M}, ainda não foi finalizado. '
                            'Acesse o GAAP para preencher e finalizar o relatório de treino.'
                        ),
                        from_email=None,
                        recipient_list=[treinador.email],
                    )
            except IntegrityError:
                continue
            except OSError as erro:
                # Falha no servidor de e-mail: o registro é desfeito e a próxima execução tenta de novo.
                self.stderr.write(f'Sessão {sessao.pk}: falha ao enviar o lembrete ({erro}).')
                continue
            enviados += 1

        self.stdout.write(self.style.SUCCESS(f'Lembretes de relatório enviados: {enviados}'))
