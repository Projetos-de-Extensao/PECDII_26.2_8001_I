---
id: rastreabilidade
title: Rastreabilidade Requisito × Artefato
---
# Rastreabilidade Requisito × Artefato

Esta matriz liga os requisitos estáveis do [levantamento](levreq.md) aos documentos em que são definidos, modelados ou representados. O [DER](der.md) complementa o modelo de classes com as tabelas propostas. As células indicam quando uma representação visual é parcial ou pendente. Uma referência não significa que a funcionalidade já esteja implementada; o [plano de viabilidade](viabilidade_mvp.md) registra o estado atual do código. RF-04 já está implementado em `/api/sessoes/`: Administrador consulta a agenda operacional; Treinador e Profissional de Saúde veem apenas os compromissos do próprio escopo e podem filtrar por serviço vinculado ao perfil.

| ID | Visão | Caso de uso | Classes/domínio | Sequência | Protótipo baixa | Protótipo alta |
|---|---|---|---|---|---|---|
| RF-01 | Objetivos/perfis | UC-01 | Usuario | Ambos (autorização) | Login | Login; estados de erro pendentes nos exports |
| RF-02 | Objetivos/perfis | UC-02 | Aluno, Usuario, Servico | — | Cadastros | Cadastros; formulário e validação pendentes nos exports |
| RF-03 | Escopo do MVP | UC-03, UC-05 | Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/configuração | Visão geral: atalho; configuração de horários e bloqueios pendente nos exports |
| RF-04 | Perfis | UC-04 | Sessao, Usuario, Servico | — | Agenda por perfil | Agenda por perfil; filtro de serviços vinculados |
| RF-05 | Escopo do MVP | UC-05 | Sessao, Servico, Participacao | Confirmar agendamento | Agenda/confirmação | Novo agendamento e variante de recusa; estado de sucesso e configuração de disponibilidade/bloqueios pendentes |
| RF-06 | Objetivos/perfis | UC-06 | Participacao | — (registro separado do relatório; sem sequência própria) | Presença no Treino e no atendimento | Minha agenda (Treino); presença/falta exemplificada nos atendimentos, ainda sem estado salvo ou erro |
| RF-07 | Objetivos/perfis | UC-07 | RelatorioTreino | Finalizar relatório | Relatório de treino | Minha agenda; campos, métricas e ações de rascunho/finalização exemplificados; falta tela finalizada somente para leitura |
| RF-08 (fora do escopo) | Fora do escopo | UC-08 | NotificacaoEmail | — | Mapa de telas; sem wireframe do e-mail | Aviso por e-mail não representado nos exports |
| RF-09 | Objetivos/perfis/MVP | UC-09 | Sessao, Participacao, RelatorioTreino | — | Visão geral e pendências | Visão geral: resumo; critério de pendência definido, mas estados visuais ainda precisam ser completados |
| RF-10 | Objetivos/perfis | UC-10 | Sessao.situacao | — | Agenda do Treinador e atendimentos | Registro realizado/não realizado definido; representação nos exports ainda pendente |
| RF-11 | Objetivos/perfis | UC-11 | Consulta agregada de Sessao por serviço e situação; sem classe própria | — | Visão geral: contagens por serviço/situação | Indicadores definidos; representação visual ainda precisa ser atualizada |
| RF-12 | Objetivos/perfis | UC-12 | Sessao, RelatorioTreino, NotificacaoEmail | — | E-mail de lembrete | Lembrete 24h após fim se relatório ausente/rascunho; fluxo ainda não representado no protótipo |
| RN-01 a RN-04 | Escopo do MVP | UC-05 | Sessao, Serviço, Disponibilidade, BloqueioAgenda | Confirmar agendamento | Agenda/confirmação | Novo agendamento e variante de recusa para indisponibilidade, bloqueio, conflito e incompatibilidade; configuração e estado de sucesso pendentes |
| RN-05 | Perfis | UC-06, UC-07 | Usuario, Participacao, RelatorioTreino | Finalizar relatório (Treino); presença sem sequência própria | Minha agenda e atendimentos | Presença no atendimento exemplificada; falta estado salvo e erro |
| RN-06 | Escopo do MVP | UC-05 | Sessao, Participacao | Confirmar agendamento | Resultado da confirmação; atomicidade interna à API | Novo agendamento; atomicidade interna à API |
| RN-07 | Objetivos/MVP | UC-05 | Aluno, Participacao, Sessao; DER participacao | Confirmar agendamento | Agenda/confirmação; validação interna | Variante de recusa exemplifica conflito do aluno; regra decidida para o MVP |
| RNF-01 | Restrições | UC-02, UC-05, UC-07 | Modelo relacional | Ambos (persistência) | — | — (modelo de dados interno à API) |
| RNF-02 | Restrições | UC-01 | Usuario | — | — (hash de senha interno à API) | — (hash de senha interno à API) |
| RNF-03 | Escopo/qualidade | UC-05 | Sessao, Participacao | Confirmar agendamento | — (concorrência e atomicidade internas à API) | — (concorrência e atomicidade internas à API) |
| RNF-04 | Restrições | UC-01 a UC-07, UC-09 a UC-11 | Usuario | Ambos | Erro de acesso/dados | Login; outros estados de erro pendentes nos exports |
| RNF-05 | Restrições | UC-01 a UC-07, UC-09 | Todos | Ambos | — (testes e documentação fora da interface) | — (testes e documentação fora da interface) |
| RNF-06 | Objetivos/qualidade | UC-02, UC-05, UC-06, UC-07, UC-10 | RegistroAuditoria com mensagem legível; DER registro_auditoria | — | Registro interno à API | Registro interno à API |
| RNF-07 | Escopo adicional do MVP do grupo | Fluxos RF-01 a RF-12 conforme perfil | Cliente web responsivo; backend continua como autoridade | Integração cliente–API | Não se aplica | Telas desktop e mobile existentes; cobertura parcial e pendências descritas no [registro de revisão](prototipo_alta_fidelidade.md#revisao-de-aderencia-para-o-front-end) |

## Lacunas de rastreabilidade

- As telas exportadas de alta fidelidade estão disponíveis na [página de prototipagem](../Iniciacao/prototipo_baixa_fidelidade.md#referencia-visual--prototipo-de-alta-fidelidade) e no [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade). A variante de recusa cobre indisponibilidade, bloqueio, conflito e incompatibilidade; o relatório contém os campos definidos. Ainda faltam o estado de sucesso do agendamento, a configuração de horários/bloqueios, estados salvo/erro da presença nos atendimentos, a tela do relatório finalizado somente para leitura e a representação de RF-10. RF-11 ainda depende da definição de indicadores. Ver [registro do protótipo](prototipo_alta_fidelidade.md).
- O professor informou capacidade máxima de 6 alunos por sessão, registrada na RN-02; Pedro Lucas esclareceu que ela vale para qualquer serviço e será validada como constante no backend do MVP, sem configuração administrativa. As definições do relatório (campos, métricas, rascunho, por sessão e imutabilidade após finalização) estão no [levantamento](levreq.md).
- Os diagramas são propostas conceituais e não demonstram, por si sós, que a implementação atual satisfaz os requisitos.
