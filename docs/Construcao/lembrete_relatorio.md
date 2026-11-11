# Lembrete de relatório pendente (RF-12)

O comando `notificar_relatorios_pendentes` envia um e-mail ao Treinador responsável quando o relatório de treino de uma sessão continua ausente ou em rascunho 24 horas depois do fim previsto da sessão.

## Quando uma sessão recebe o lembrete

A sessão precisa atender a todas as condições:

- é do serviço de categoria **Treino** (atendimentos de saúde nunca recebem lembrete);
- está com a situação **Realizada**, pois o relatório só pode ser criado depois dessa marcação (mesma regra da pendência de relatório do RF-09);
- terminou há pelo menos 24 horas;
- não tem relatório ou tem relatório em **rascunho**;
- o responsável é um Treinador com e-mail cadastrado;
- ainda não recebeu este lembrete.

Uma sessão que continua **Agendada** depois do horário não recebe este lembrete: a pendência dela é de situação e é avisada pelo comando `notificar_sessoes_pendentes` (RF-08).

## Como a duplicidade é evitada

Cada envio grava uma linha na tabela `NotificacaoEmail` com a sessão e o tipo `RELATORIO_PENDENTE`. O par `(sessao, tipo)` é único no banco.

1. O comando grava o registro e envia o e-mail na mesma transação.
2. Se outra execução já gravou o registro, o banco recusa a segunda gravação e o e-mail não sai.
3. Se o servidor de e-mail falhar, a transação é desfeita e a próxima execução tenta de novo.

## Configuração

O envio usa as variáveis de e-mail do `.env` (ver `backend/src/.env.example`):

| Variável | Uso |
|---|---|
| `EMAIL_BACKEND` | `console` em desenvolvimento; `smtp` para envio real |
| `DEFAULT_FROM_EMAIL` | Remetente dos lembretes |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | Dados do servidor SMTP |

## Operação

Execução manual, a partir de `backend/src/`:

```bash
python manage.py notificar_relatorios_pendentes
```

Na VPS, o timer `pbe-notificar-relatorios.timer` executa o comando a cada 15 minutos. O workflow de deploy instala e habilita o timer. Para conferir:

```bash
systemctl list-timers pbe-notificar-relatorios.timer
journalctl -u pbe-notificar-relatorios.service --since today
```

Para ver os lembretes já enviados:

```bash
python manage.py shell -c "from app.models import NotificacaoEmail; print(list(NotificacaoEmail.objects.values('sessao_id', 'tipo', 'enviada_em')))"
```
