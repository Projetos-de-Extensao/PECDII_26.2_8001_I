import django.db.models.deletion
from django.db import migrations, models


def recusar_sessoes_incompletas(apps, schema_editor):
    """Interrompe a migração se ainda houver sessão sem serviço ou sem profissional.

    As colunas ficaram opcionais por causa das sessões criadas antes do catálogo (0012 e 0014).
    O destino dessas sessões (apagar, completar ou manter opcional) é decisão do grupo, então a
    migração não altera dados: ela para com uma mensagem clara em vez de falhar no meio da
    reconstrução da tabela.
    """
    Sessao = apps.get_model('app', 'Sessao')
    sem_servico = Sessao.objects.filter(servico__isnull=True).count()
    sem_profissional = Sessao.objects.filter(profissional__isnull=True).count()
    if sem_servico or sem_profissional:
        raise RuntimeError(
            'Não é possível tornar serviço e profissional obrigatórios na sessão: '
            f'{sem_servico} sessão(ões) sem serviço e {sem_profissional} sem profissional. '
            'Complete ou remova essas sessões antes de aplicar a migração 0015.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_participacao_servico_da_sessao'),
    ]

    operations = [
        migrations.RunPython(recusar_sessoes_incompletas, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sessao',
            name='servico',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sessoes',
                to='app.servico',
                verbose_name='serviço',
            ),
        ),
        migrations.AlterField(
            model_name='sessao',
            name='profissional',
            field=models.ForeignKey(
                limit_choices_to={'perfil__in': ['TREINADOR', 'PROFISSIONAL_SAUDE']},
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sessoes',
                to='app.usuario',
            ),
        ),
    ]
