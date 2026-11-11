# Trilha de auditoria (RNF-06)

A API grava um registro de auditoria sempre que uma operação crítica é concluída. O registro é gravado na mesma transação da operação: se a operação falhar ou for recusada, nada é registrado.

## Eventos auditados

| Operação (`operacao`) | Quando é registrada | Entidade | Exemplo de mensagem |
|---|---|---|---|
| `USUARIO_CRIADO` | `POST /api/profissionais/` ou cadastro de usuário no Django Admin | `Usuario` | Carla Admin criou o usuário "Diego" com o perfil Treinador. |
| `AGENDAMENTO_CONFIRMADO` | `POST /api/sessoes/` aceito | `Sessao` | Carla Admin confirmou o agendamento "Treino de força" em 16/11/2026 às 06:00 com 2 aluno(s), sob responsabilidade de Diego. |
| `PRESENCA_ALTERADA` | `PATCH /api/sessoes/{id}/presencas/` que muda pelo menos uma presença | `Sessao` | Diego registrou presença/falta na sessão "Treino de força" — Ana Lima: presente; Bruno Costa: falta. |
| `RELATORIO_FINALIZADO` | `POST /api/sessoes/{id}/relatorio/finalizar/` aceito | `RelatorioTreino` | Diego finalizou o relatório de treino da sessão "Treino de força". |

Reenviar a mesma presença, sem mudança, não gera um registro novo.

## Campos de cada registro

| Campo | Conteúdo |
|---|---|
| `usuario` | Usuário GAAP autor da operação; fica vazio para o superusuário do Django sem perfil GAAP |
| `autor` | Nome do autor no momento da operação (ou o login do superusuário). Continua guardado se o usuário for removido |
| `operacao` / `operacao_rotulo` | Código e nome da operação |
| `entidade` / `entidade_id` | Tipo e ID do registro afetado |
| `mensagem` | Frase em linguagem humana |
| `registrado_em` | Data e hora da gravação |

Senhas, hashes, tokens e logins de acesso não entram em nenhum campo: as mensagens são montadas só com nome, perfil, título, data e presença.

## Imutabilidade

- A API expõe a auditoria somente para leitura: `POST`, `PUT`, `PATCH` e `DELETE` em `/api/auditoria/` respondem `405`.
- O modelo `RegistroAuditoria` recusa `save()` de um registro já gravado e `delete()`.
- No Django Admin a lista é somente leitura (sem incluir, alterar ou apagar).

## Como consultar

Somente o Administrador consulta a auditoria; os outros perfis recebem `403`.

```http
GET /api/auditoria/
GET /api/auditoria/?operacao=PRESENCA_ALTERADA
GET /api/auditoria/?entidade=Sessao&entidade_id=12
GET /api/auditoria/{id}/
```

Os registros vêm do mais recente para o mais antigo. No Django Admin, a lista **Registros de auditoria** permite filtrar por operação e entidade e buscar por autor ou mensagem.

## Limites conhecidos

- Alterações feitas direto no Django Admin em sessões e participações não são auditadas; o fluxo oficial é a API.
- O bloqueio de alteração vale para a aplicação. Quem tem acesso direto ao banco ainda consegue mudar a tabela.
