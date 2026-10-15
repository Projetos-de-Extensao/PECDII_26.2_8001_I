from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Sessao


class Command(BaseCommand):
    """Notifica professores sobre sessões ainda marcadas como agendadas."""

    help = 'Notifica professores sobre sessões agendadas após o horário previsto.'

    def handle(self, *args, **options):
        """Notifica uma vez cada sessão agendada após 30 minutos do fim."""
        limite = timezone.now() - timedelta(minutes=30)
        sessoes = Sessao.objects.filter(
            status=Sessao.Status.AGENDADA,
            notificacao_enviada_em__isnull=True,
            fim__lte=limite,
            professor__isnull=False,
        ).select_related('professor')

        notificadas = 0
        for sessao in sessoes:
            if not sessao.professor.email:
                self.stderr.write(f'Sessão {sessao.pk}: professor sem e-mail; aviso ignorado.')
                continue

            send_mail(
                subject=f'Atualize o status da sessão: {sessao.titulo}',
                message=(
                    f'A sessão "{sessao.titulo}" terminou às {sessao.fim:%d/%m/%Y %H:%M} '
                    'e ainda está marcada como agendada. Atualize o status da sessão na API.'
                ),
                from_email=None,
                recipient_list=[sessao.professor.email],
                fail_silently=False,
            )
            sessao.notificacao_enviada_em = timezone.now()
            sessao.save(update_fields=['notificacao_enviada_em'])
            notificadas += 1

        self.stdout.write(self.style.SUCCESS(f'Notificações enviadas: {notificadas}'))
