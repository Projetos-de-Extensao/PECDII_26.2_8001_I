---
id: rastreabilidade
title: Rastreabilidade Requisito × Artefato
---
# Rastreabilidade Requisito × Artefato

Esta matriz liga os requisitos estáveis do [levantamento](levreq.md) aos documentos em que são definidos, modelados ou representados. Uma referência não significa que a funcionalidade já esteja implementada; o [plano de viabilidade](viabilidade_mvp.md) registra o estado atual do código.

| ID | Visão | Caso de uso | Classes/domínio | Sequência | Protótipo baixa | Protótipo alta |
|---|---|---|---|---|---|---|
| RF-01 | Objetivos/perfis | UC-01 | Usuario | Finalizar relatório (autorização) | Login | Login |
| RF-02 | Objetivos/perfis | UC-02 | Aluno, Usuario, Servico | — | Cadastros | Cadastros |
| RF-03 | Escopo do MVP | UC-03, UC-05 | Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/configuração | Agenda/configuração |
| RF-04 | Perfis | UC-04 | Sessao, Usuario | — | Agenda por perfil | Agenda por perfil |
| RF-05 | Escopo do MVP | UC-05 | Sessao, Servico, Participacao | Confirmar agendamento | Agenda/confirmação | Confirmação |
| RF-06 | Objetivos/perfis | UC-06 | Participacao | Registrar presença/falta em sessão ou atendimento | Presença/relatório | Presença/relatório |
| RF-07 | Objetivos/perfis | UC-07 | RelatorioTreino | Finalizar relatório | Presença/relatório | Presença/relatório |
| RF-08 (fora do escopo) | Fora do escopo | UC-08 | NotificacaoEmail | — | Aviso pendente | Aviso pendente |
| RN-01 a RN-04 | Escopo do MVP | UC-05 | Sessao, Serviço, Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/confirmação | Confirmação |
| RN-05 | Perfis | UC-01, UC-04, UC-06, UC-07 | Usuario | Ambos | Login, agendas, relatório | Login, agendas, relatório |
| RN-06 | Escopo do MVP | UC-05, UC-07 | Sessao, Participacao, RelatorioTreino | Ambos | Resultado da confirmação/relatório | Estados de sucesso e erro |
| RNF-01 | Restrições | UC-02, UC-05, UC-07 | Modelo relacional | Ambos | — | Cadastros/fluxos |
| RNF-02 | Restrições | UC-01 | Usuario | — | Login | Login |
| RNF-03 | Escopo/qualidade | UC-05, UC-07 | Sessao, RelatorioTreino | Ambos | Erros de validação | Estados de erro |
| RNF-04 | Restrições | UC-01 a UC-07 | Usuario | Ambos | Erro de acesso/dados | Estados de acesso/dados |
| RNF-05 | Restrições | UC-01 a UC-07 | Todos | Ambos | Todos os fluxos | Todos os fluxos |

## Lacunas de rastreabilidade

- As telas exportadas de alta fidelidade estão disponíveis na [página de prototipagem](../Iniciacao/prototipo_baixa_fidelidade.md#referencia-visual--prototipo-de-alta-fidelidade) e no [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade). A correspondência tela a tela com todos os IDs e estados ainda precisa ser revisada. Ver [registro do protótipo](prototipo_alta_fidelidade.md).
- O cliente/responsável pelo cenário ainda precisa definir capacidade. As definições do relatório (campos, métricas, rascunho, por sessão e imutabilidade após finalização) estão no [levantamento](levreq.md).
- Os diagramas são propostas conceituais e não demonstram, por si sós, que a implementação atual satisfaz os requisitos.
