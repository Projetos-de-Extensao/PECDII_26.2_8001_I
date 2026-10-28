---
id: rastreabilidade
title: Rastreabilidade Requisito × Artefato
---
# Rastreabilidade Requisito × Artefato

Esta matriz liga os requisitos estáveis do [levantamento](levreq.md) aos documentos em que são definidos, modelados ou representados. As células indicam quando uma representação visual é parcial ou pendente. Uma referência não significa que a funcionalidade já esteja implementada; o [plano de viabilidade](viabilidade_mvp.md) registra o estado atual do código.

| ID | Visão | Caso de uso | Classes/domínio | Sequência | Protótipo baixa | Protótipo alta |
|---|---|---|---|---|---|---|
| RF-01 | Objetivos/perfis | UC-01 | Usuario | Ambos (autorização) | Login | Login; estados de erro pendentes nos exports |
| RF-02 | Objetivos/perfis | UC-02 | Aluno, Usuario, Servico | — | Cadastros | Cadastros; formulário e validação pendentes nos exports |
| RF-03 | Escopo do MVP | UC-03, UC-05 | Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/configuração | Visão geral: atalho; configuração de horários e bloqueios pendente nos exports |
| RF-04 | Perfis | UC-04 | Sessao, Usuario | — | Agenda por perfil | Agenda por perfil |
| RF-05 | Escopo do MVP | UC-05 | Sessao, Servico, Participacao | Confirmar agendamento | Agenda/confirmação | Novo agendamento; estados de erro pendentes nos exports |
| RF-06 | Objetivos/perfis | UC-06 | Participacao | Finalizar relatório (Treino); atendimento sem sequência própria | Presença no Treino e no atendimento | Minha agenda (Treino); presença no atendimento pendente nos exports |
| RF-07 | Objetivos/perfis | UC-07 | RelatorioTreino | Finalizar relatório | Relatório de treino | Minha agenda; campos e estados do relatório pendentes nos exports |
| RF-08 (fora do escopo) | Fora do escopo | UC-08 | NotificacaoEmail | — | Mapa de telas; sem wireframe do e-mail | Aviso por e-mail não representado nos exports |
| RN-01 a RN-04 | Escopo do MVP | UC-05 | Sessao, Serviço, Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/confirmação | Novo agendamento; estados de erro pendentes nos exports |
| RN-05 | Perfis | UC-06, UC-07 | Usuario, Participacao, RelatorioTreino | Finalizar relatório (Treino); atendimento sem sequência própria | Minha agenda e atendimentos | Minha agenda; presença no atendimento pendente nos exports |
| RN-06 | Escopo do MVP | UC-05 | Sessao, Participacao | Confirmar agendamento | Resultado da confirmação; atomicidade interna à API | Novo agendamento; atomicidade interna à API |
| RNF-01 | Restrições | UC-02, UC-05, UC-07 | Modelo relacional | Ambos (persistência) | — | — (modelo de dados interno à API) |
| RNF-02 | Restrições | UC-01 | Usuario | — | — (hash de senha interno à API) | — (hash de senha interno à API) |
| RNF-03 | Escopo/qualidade | UC-05 | Sessao, Participacao | Confirmar agendamento | — (concorrência e atomicidade internas à API) | — (concorrência e atomicidade internas à API) |
| RNF-04 | Restrições | UC-01 a UC-07 | Usuario | Ambos | Erro de acesso/dados | Login; outros estados de erro pendentes nos exports |
| RNF-05 | Restrições | UC-01 a UC-07 | Todos | Ambos | — (testes e documentação fora da interface) | — (testes e documentação fora da interface) |

## Lacunas de rastreabilidade

- As telas exportadas de alta fidelidade estão disponíveis na [página de prototipagem](../Iniciacao/prototipo_baixa_fidelidade.md#referencia-visual--prototipo-de-alta-fidelidade) e no [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade). Ainda faltam as representações de presença/falta em atendimentos de saúde, dos campos e estados do relatório de treino, da configuração de horários/bloqueios e dos estados de erro do agendamento. Ver [registro do protótipo](prototipo_alta_fidelidade.md).
- O cliente/responsável pelo cenário ainda precisa definir capacidade. As definições do relatório (campos, métricas, rascunho, por sessão e imutabilidade após finalização) estão no [levantamento](levreq.md).
- Os diagramas são propostas conceituais e não demonstram, por si sós, que a implementação atual satisfaz os requisitos.
